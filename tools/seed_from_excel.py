"""
从 XLS 文件导入学生及答案数据到 MindWise 数据库。

Sheet0 格式（第一行为表头）：
  学号 | 姓名 | 性别 | 班级 | 1 | 2 | ... | 93
  （第 5 列起为各题答案，对应数据库中第 1-93 题）

使用方法（从 mindwise-api/ 目录运行）：
  python tools/seed_from_excel.py <xls路径> [--exam-id N] [--reset]

选项：
  --exam-id N   目标考试 ID（默认：1）
  --reset       导入前清空所有学生、答案及评分数据
"""
import sys
import os
import argparse

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from app.db.session import SessionLocal
from app.models.student import Student
from app.models.class_ import Class
from app.models.answer import Answer
from app.models.score_student import ScoreStudent
from app.models.question import Question
from app.models.exam import Exam
from app.models.teacher import Teacher


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
    print(f"  已删除: {answers_deleted} 条答案, {scores_deleted} 条评分, "
          f"{students_deleted} 名学生, {classes_deleted} 个班级")


def run(xls_path: str, exam_id: int, reset: bool):
    db = SessionLocal()
    try:
        if reset:
            print("重置学生数据...")
            reset_student_data(db)

        # 验证考试存在
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            print(f"ERROR: 考试 ID={exam_id} 不存在，请先在数据库中创建考试记录")
            return

        # 读取 Excel
        df = pd.read_excel(xls_path, sheet_name="Sheet0", header=0)
        # 统一列名：前4列为元数据，其余为答题列
        df = df.rename(columns={
            df.columns[0]: "student_no",
            df.columns[1]: "name",
            df.columns[2]: "gender",
            df.columns[3]: "class_name",
        })
        answer_cols = df.columns[4:].tolist()  # 实际列名（可能是 1.0, 2.0 等）

        df = df.dropna(subset=["student_no", "name", "class_name"])
        print(f"读取到有效学生: {len(df)} 名，题目列数: {len(answer_cols)}")

        # 获取数据库题目 ID（按 ID 升序）
        q_ids = [q.id for q in db.query(Question).order_by(Question.id).all()]
        if len(q_ids) < len(answer_cols):
            print(f"WARNING: 数据库题目数 {len(q_ids)} 少于 Excel 答题列数 {len(answer_cols)}，"
                  f"只处理前 {len(q_ids)} 列")
            answer_cols = answer_cols[:len(q_ids)]

        # 创建/复用班级
        class_map = {c.name: c.id for c in db.query(Class).all()}
        for cname in df["class_name"].unique():
            cname = str(cname).strip()
            if cname not in class_map:
                new_class = Class(name=cname)
                db.add(new_class)
                db.flush()
                class_map[cname] = new_class.id
                print(f"  新建班级: {cname} (id={new_class.id})")
        db.commit()

        # 插入学生及答案
        students_added = 0
        answers_added = 0

        for _, row in df.iterrows():
            cname = str(row["class_name"]).strip()
            gender = str(row["gender"]).strip() if pd.notna(row["gender"]) else "未知"
            name = str(row["name"]).strip()

            student = Student(name=name, gender=gender, class_id=class_map[cname])
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
        print(f"\n完成！插入学生: {students_added} 名，答案: {answers_added} 条")

    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从 XLS 文件导入学生及答案数据")
    parser.add_argument("xls_path", help="XLS 文件路径")
    parser.add_argument("--exam-id", type=int, default=1, help="目标考试 ID（默认：1）")
    parser.add_argument("--reset", action="store_true",
                        help="导入前清空所有学生、答案、评分数据（保留教师绑定的班级）")
    args = parser.parse_args()
    run(args.xls_path, args.exam_id, args.reset)
