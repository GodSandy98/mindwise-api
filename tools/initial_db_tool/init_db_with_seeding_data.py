# init_db_with_seeding_data.py
import json
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

from app.core.database import Base, engine, SessionLocal
from app.models import (
    Class, Student, Exam, Indicator, Question, Answer,
    PersonaTemplate, IndicatorText,
)
from app.models.indicator_question import IndicatorQuestion

# 0. Load JSON fixtures
with open("./default_indicators.json", encoding="utf-8") as f:
    DEFAULT_INDICATORS = json.load(f)

with open("./default_indicator_question.json", encoding="utf-8") as f:
    DEFAULT_INDICATOR_QUESTION = json.load(f)

with open("./default_questions.json", encoding="utf-8") as f:
    DEFAULT_QUESTIONS = json.load(f)

with open("./default_answers.json", encoding="utf-8") as f:
    DEFAULT_ANSWERS = json.load(f)

with open("./default_persona_templates.json", encoding="utf-8") as f:
    DEFAULT_PERSONAS = json.load(f)

with open("./default_indicator_texts.json", encoding="utf-8") as f:
    DEFAULT_INDICATOR_TEXTS = json.load(f)

# 1. Create tables
Base.metadata.create_all(bind=engine)
print("✅ 表结构已创建")

# 2. Seed data
db = SessionLocal()
try:
    # --- Classes & Students ---
    if db.query(Class).count() == 0:
        cls = Class(name="高一(3)班")
        db.add(cls)
        db.commit()
        db.refresh(cls)

        student = Student(name="张三", gender="男", class_id=cls.id)
        db.add(student)
        db.commit()
        print("✅ 测试学生、班级数据已插入")
    else:
        print("ℹ️ 学生、班级数据已存在，跳过")

    # --- Exams ---
    if db.query(Exam).count() == 0:
        exam = Exam(name="2025年度期中全校心理测试", date=datetime(2025, 10, 15, 10, 0, 0))
        db.add(exam)
        db.commit()
        print("✅ 测试考试数据已插入")
    else:
        print("ℹ️ 考试数据已存在，跳过")

    # --- Indicators (with parent_id, system, is_leaf) ---
    if db.query(Indicator).count() == 0:
        for data in DEFAULT_INDICATORS:
            db.add(Indicator(**data))
        db.commit()
        print(f"✅ {len(DEFAULT_INDICATORS)} 条指标数据已插入")
    else:
        print("ℹ️ 指标数据已存在，跳过")

    # --- Questions ---
    if db.query(Question).count() == 0:
        for data in DEFAULT_QUESTIONS:
            db.add(Question(**data))
        db.commit()
        print(f"✅ {len(DEFAULT_QUESTIONS)} 条问题数据已插入")
    else:
        print("ℹ️ 问题数据已存在，跳过")

    # --- Indicator-Question mappings (leaf-only) ---
    if db.query(IndicatorQuestion).count() == 0:
        for data in DEFAULT_INDICATOR_QUESTION:
            db.add(IndicatorQuestion(**data))
        db.commit()
        print(f"✅ {len(DEFAULT_INDICATOR_QUESTION)} 条指标-问题关系已插入")
    else:
        print("ℹ️ 指标-问题关系已存在，跳过")

    # --- Answers ---
    if db.query(Answer).count() == 0:
        for data in DEFAULT_ANSWERS:
            db.add(Answer(**data))
        db.commit()
        print(f"✅ {len(DEFAULT_ANSWERS)} 条回答数据已插入")
    else:
        print("ℹ️ 回答数据已存在，跳过")

    # --- Persona Templates (27 archetypes) ---
    if db.query(PersonaTemplate).count() == 0:
        for data in DEFAULT_PERSONAS:
            db.add(PersonaTemplate(**data))
        db.commit()
        print(f"✅ {len(DEFAULT_PERSONAS)} 条画像模板已插入")
    else:
        print("ℹ️ 画像模板已存在，跳过")

    # --- Indicator Texts (17 leaves × 3 levels × 2 views = 102) ---
    if db.query(IndicatorText).count() == 0:
        for i, data in enumerate(DEFAULT_INDICATOR_TEXTS, 1):
            db.add(IndicatorText(
                id=i,
                indicator_id=data["indicator_id"],
                level=data["level"],
                view=data["view"],
                analysis=data["analysis"],
                suggestion=data["suggestion"],
                golden_quote=data.get("golden_quote", ""),
            ))
        db.commit()
        print(f"✅ {len(DEFAULT_INDICATOR_TEXTS)} 条指标话术模板已插入")
    else:
        print(f"ℹ️ 指标话术模板已存在 ({db.query(IndicatorText).count()} 条)")

finally:
    db.close()

print("\n🎉 数据库初始化完成")
