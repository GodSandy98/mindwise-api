# init_db_with_seeding_data.py
import json
from datetime import datetime

from app.core.database import Base, engine, SessionLocal
from app.models import Class, Student, Exam, Indicator, Question, Answer
from app.models.indicator_question import IndicatorQuestion

# 0.预处理 加载 JSON 文件
with open("./default_indicators.json", encoding="utf-8") as f:
    DEFAULT_INDICATORS = json.load(f)

with open("./default_indicator_question.json", encoding="utf-8") as f:
    DEFAULT_INDICATOR_QUESTION = json.load(f)

with open("./default_questions.json", encoding="utf-8") as f:
    DEFAULT_QUESTIONS = json.load(f)

with open("./default_answers.json", encoding="utf-8") as f:
    DEFAULT_ANSWERS = json.load(f)

# 1. 创建表
Base.metadata.create_all(bind=engine)
print("✅ 表结构已创建")

# 2. 插入测试数据
db = SessionLocal()
try:
    # --- 班级 & 学生 ---
    if db.query(Class).count() == 0:
        cls = Class(name="高一(3)班")
        db.add(cls)
        db.commit()
        db.refresh(cls)

        student = Student(name="张三", gender="男", class_id=cls.id)
        db.add(student)
        db.commit()
        print("✅ 测试学生（student）、班级（class）数据已插入")
    else:
        print("ℹ️ 学生（student）、班级（class）数据已存在，跳过插入")

    # --- 考试 ---
    if db.query(Exam).count() == 0:
        exam = Exam(name="2025年度期中全校心理测试", date=datetime(2025, 10, 15, 10, 0, 0))
        db.add(exam)
        db.commit()
        print("✅ 测试考试（Exam）数据已插入")
    else:
        print("ℹ️ 考试（Exam）数据已存在，跳过插入")

    # --- 指标---
    if db.query(Indicator).count() == 0:
        for data in DEFAULT_INDICATORS:
            db.add(Indicator(**data))
        db.commit()
        print(f"✅ {len(DEFAULT_INDICATORS)} 条测试指标（indicator）数据已插入")
    else:
        print("ℹ️ 指标（indicator）数据已存在，跳过插入")

    # --- 问题---
    if db.query(Question).count() == 0:
        for data in DEFAULT_QUESTIONS:
            db.add(Question(**data))
        db.commit()
        print(f"✅ {len(DEFAULT_QUESTIONS)} 条测试问题（question）数据已插入")
    else:
        print("ℹ️ 问题（question）数据已存在，跳过插入")

    # --- 指标问题关系（依赖 Indicator、Question 已存在）---
    if db.query(IndicatorQuestion).count() == 0:
        for data in DEFAULT_INDICATOR_QUESTION:
            db.add(IndicatorQuestion(**data))
        db.commit()
        print(f"✅ {len(DEFAULT_INDICATOR_QUESTION)} 条测试指标问题关系（indicator_question）数据已插入")
    else:
        print("ℹ️ 指标问题关系（indicator_question）数据已存在，跳过插入")

    # --- 回答（依赖 Student、Question、Exam 已存在）---
    if db.query(Answer).count() == 0:
        for data in DEFAULT_ANSWERS:
            db.add(Answer(**data))
        db.commit()
        print(f"✅ {len(DEFAULT_ANSWERS)} 条测试回答（answer）数据已插入")
    else:
        print("ℹ️ 回答（answer）数据已存在，跳过插入")
finally:
    db.close()