# import_questions.py
import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from contextlib import contextmanager

from app.models.question import Question

DATABASE_URL = "sqlite:///../../mindwise.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def import_questions_from_json(json_path: str, clear_existing: bool = False):
    """
    从 JSON 文件导入题目到数据库
    :param json_path: JSON 文件路径
    :param clear_existing: 是否先清空现有题目（谨慎使用！）
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    questions_data = data.get("questions", [])
    if not questions_data:
        print("❌ JSON 中没有找到 questions 字段或为空")
        return

    with get_db() as db:
        try:
            # 可选：清空旧数据（测试时用）
            if clear_existing:
                db.query(Question).delete()
                print("🗑️ 已清空 questions 表")

            # 批量创建对象
            new_questions = []
            for item in questions_data:
                q = Question(
                    name=item["text"],
                    num_choices=item["num_choices"],
                    is_negative=item["is_negative"]
                )
                new_questions.append(q)

            db.add_all(new_questions)
            db.commit()
            print(f"✅ 成功导入 {len(new_questions)} 道题目到数据库")

        except Exception as e:
            db.rollback()
            print(f"❌ 导入失败: {e}")
            raise

if __name__ == "__main__":
    JSON_FILE = "questions.json"
    CLEAR_EXISTING = True  # 设为 True 会删除所有旧题目！
    import_questions_from_json(JSON_FILE, clear_existing=CLEAR_EXISTING)