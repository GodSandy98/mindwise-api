"""
Seed students and answers from Excel file.
- Deletes existing test students (id=1, id=2) and their data
- Creates classes from Excel if not existing
- Creates students and their answers for exam_id=1
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from app.db.session import SessionLocal
from app.models.student import Student
from app.models.class_ import Class
from app.models.answer import Answer
from app.models.score_student import ScoreStudent

EXCEL_PATH = "/Users/yubosong/Desktop/MindWise项目资料/claude_seed_data.xls"
EXAM_ID = 1
TEST_STUDENT_IDS = [1, 2]

def run():
    db = SessionLocal()
    try:
        # 1. Delete test students' related data
        print("删除测试学生数据...")
        for sid in TEST_STUDENT_IDS:
            db.query(Answer).filter(Answer.student_id == sid).delete()
            db.query(ScoreStudent).filter(ScoreStudent.student_id == sid).delete()
            db.query(Student).filter(Student.id == sid).delete()
        db.commit()
        print(f"  已删除 {len(TEST_STUDENT_IDS)} 个测试学生")

        # 2. Read Excel
        df = pd.read_excel(EXCEL_PATH, sheet_name="Sheet0")
        df = df.dropna(subset=["学号", "姓名", "班级"])
        print(f"Excel 有效学生数: {len(df)}")

        # 3. Create/get classes
        class_map = {}  # name -> id
        existing_classes = {c.name: c.id for c in db.query(Class).all()}
        excel_classes = df["班级"].unique().tolist()

        for cname in excel_classes:
            if cname in existing_classes:
                class_map[cname] = existing_classes[cname]
            else:
                new_class = Class(name=cname)
                db.add(new_class)
                db.flush()
                class_map[cname] = new_class.id
                print(f"  新建班级: {cname} (id={new_class.id})")
        db.commit()

        # 4. Get question IDs (1..93)
        from app.models.question import Question
        questions = db.query(Question).order_by(Question.id).all()
        q_ids = [q.id for q in questions]
        if len(q_ids) != 93:
            print(f"WARNING: 数据库题目数量={len(q_ids)}，期望93")

        # 5. Insert students and answers
        print("插入学生和答案...")
        gender_map = {"男": "M", "女": "F"}
        answer_cols = [str(i) for i in range(1, 94)]

        students_added = 0
        answers_added = 0

        for _, row in df.iterrows():
            class_id = class_map.get(row["班级"])
            gender = gender_map.get(str(row.get("性别", "")).strip(), "M")

            student = Student(
                name=str(row["姓名"]).strip(),
                gender=gender,
                class_id=class_id,
            )
            db.add(student)
            db.flush()
            students_added += 1

            for i, col in enumerate(answer_cols):
                val = row.get(col)
                if pd.notna(val):
                    ans = Answer(
                        student_id=student.id,
                        exam_id=EXAM_ID,
                        question_id=q_ids[i],
                        answer=int(val),
                    )
                    db.add(ans)
                    answers_added += 1

        db.commit()
        print(f"完成！插入学生: {students_added}，答案: {answers_added}")

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    run()
