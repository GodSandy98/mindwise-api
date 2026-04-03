"""
从 XLS 文件导入学生及答案数据到 MindWise 数据库。
自动完成建表、基础数据初始化（指标/题目/考试），无需提前运行其他脚本。

Sheet0 格式（第一行为表头）：
  学号 | 姓名 | 性别 | 班级 | 1 | 2 | ... | 93

使用方法（从 mindwise-api/ 目录运行）：
  python tools/seed_from_excel.py <xls路径> [选项]

选项：
  --exam-name NAME    考试名称，不存在则自动创建（默认：全校心理测评）
  --exam-date DATE    考试日期 YYYY-MM-DD，仅新建考试时使用（默认：今天）
  --reset             导入前清空所有学生、答案及评分数据
"""
import sys
import os
import argparse
import json
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from app.core.database import Base, engine, SessionLocal
from app.models import Class, Student, Exam, Indicator, Question, Answer
from app.models.indicator_question import IndicatorQuestion
from app.models.score_student import ScoreStudent
from app.models.teacher import Teacher

# JSON 基础数据路径（相对于本脚本所在目录）
_FIXTURE_DIR = Path(__file__).parent / "initial_db_tool"


def ensure_schema():
    """建表（已存在则跳过）"""
    Base.metadata.create_all(bind=engine)
    print("✅ 表结构就绪")


def ensure_base_data(db):
    """确保指标、题目、指标-题目映射存在，不存在则从 JSON 写入"""
    def load(name):
        with open(_FIXTURE_DIR / name, encoding="utf-8") as f:
            return json.load(f)

    if db.query(Indicator).count() == 0:
        data = load("default_indicators.json")
        for row in data:
            db.add(Indicator(**row))
        db.commit()
        print(f"  ✅ 插入 {len(data)} 个心理指标")
    else:
        print("  ℹ️  心理指标已存在，跳过")

    if db.query(Question).count() == 0:
        data = load("default_questions.json")
        for row in data:
            db.add(Question(**row))
        db.commit()
        print(f"  ✅ 插入 {len(data)} 道题目")
    else:
        print("  ℹ️  题目已存在，跳过")

    if db.query(IndicatorQuestion).count() == 0:
        data = load("default_indicator_question.json")
        for row in data:
            db.add(IndicatorQuestion(**row))
        db.commit()
        print(f"  ✅ 插入 {len(data)} 条指标-题目映射")
    else:
        print("  ℹ️  指标-题目映射已存在，跳过")


def ensure_exam(db, exam_name: str, exam_date: datetime) -> Exam:
    """获取指定名称的考试，不存在则创建"""
    exam = db.query(Exam).filter(Exam.name == exam_name).first()
    if exam:
        print(f"  ℹ️  考试「{exam_name}」已存在（id={exam.id}），跳过创建")
    else:
        exam = Exam(name=exam_name, date=exam_date)
        db.add(exam)
        db.commit()
        db.refresh(exam)
        print(f"  ✅ 创建考试「{exam_name}」（id={exam.id}）")
    return exam


def reset_student_data(db):
    answers_deleted = db.query(Answer).delete()
    scores_deleted = db.query(ScoreStudent).delete()
    students_deleted = db.query(Student).delete()

    used_class_ids = {t.class_id for t in db.query(Teacher).all() if t.class_id}
    classes_deleted = 0
    for cls in db.query(Class).all():
        if cls.id not in used_class_ids:
            db.delete(cls)
            classes_deleted += 1
    db.commit()
    print(f"  已清空：{answers_deleted} 条答案，{scores_deleted} 条评分，"
          f"{students_deleted} 名学生，{classes_deleted} 个班级")


def import_students(db, xls_path: str, exam_id: int):
    df = pd.read_excel(xls_path, sheet_name="Sheet0", header=0)
    df = df.rename(columns={
        df.columns[0]: "student_no",
        df.columns[1]: "name",
        df.columns[2]: "gender",
        df.columns[3]: "class_name",
    })
    answer_cols = df.columns[4:].tolist()
    df = df.dropna(subset=["student_no", "name", "class_name"])
    print(f"  读取到有效学生 {len(df)} 名，答题列 {len(answer_cols)} 列")

    q_ids = [q.id for q in db.query(Question).order_by(Question.id).all()]
    if len(q_ids) < len(answer_cols):
        print(f"  ⚠️  题目数 {len(q_ids)} < 答题列数 {len(answer_cols)}，只处理前 {len(q_ids)} 列")
        answer_cols = answer_cols[:len(q_ids)]

    class_map = {c.name: c.id for c in db.query(Class).all()}
    for cname in df["class_name"].unique():
        cname = str(cname).strip()
        if cname not in class_map:
            new_cls = Class(name=cname)
            db.add(new_cls)
            db.flush()
            class_map[cname] = new_cls.id
            print(f"  新建班级：{cname}（id={new_cls.id}）")
    db.commit()

    students_added = answers_added = 0
    for _, row in df.iterrows():
        student = Student(
            name=str(row["name"]).strip(),
            gender=str(row["gender"]).strip() if pd.notna(row["gender"]) else "未知",
            class_id=class_map[str(row["class_name"]).strip()],
        )
        db.add(student)
        db.flush()
        students_added += 1

        for i, col in enumerate(answer_cols):
            val = row[col]
            if pd.notna(val):
                try:
                    db.add(Answer(
                        student_id=student.id,
                        exam_id=exam_id,
                        question_id=q_ids[i],
                        answer=int(float(val)),
                    ))
                    answers_added += 1
                except (ValueError, TypeError):
                    pass

    db.commit()
    print(f"  ✅ 导入学生 {students_added} 名，答案 {answers_added} 条")


def run(xls_path: str, exam_name: str, exam_date: datetime, reset: bool):
    print("\n── 第一步：建表 ──────────────────────────")
    ensure_schema()

    db = SessionLocal()
    try:
        print("\n── 第二步：基础数据 ───────────────────────")
        ensure_base_data(db)

        print("\n── 第三步：考试记录 ───────────────────────")
        exam = ensure_exam(db, exam_name, exam_date)

        if reset:
            print("\n── 清空旧学生数据 ─────────────────────────")
            reset_student_data(db)

        print("\n── 第四步：导入学生与答案 ──────────────────")
        import_students(db, xls_path, exam.id)

        print("\n🎉 完成！")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="一键初始化数据库并从 XLS 导入学生数据")
    parser.add_argument("xls_path", help="XLS 文件路径")
    parser.add_argument("--exam-name", default="全校心理测评", help="考试名称（默认：全校心理测评）")
    parser.add_argument("--exam-date", default=datetime.today().strftime("%Y-%m-%d"),
                        help="考试日期 YYYY-MM-DD（默认：今天）")
    parser.add_argument("--reset", action="store_true",
                        help="导入前清空所有学生、答案、评分数据（保留教师绑定的班级）")
    args = parser.parse_args()

    exam_date = datetime.strptime(args.exam_date, "%Y-%m-%d")
    run(args.xls_path, args.exam_name, exam_date, args.reset)
