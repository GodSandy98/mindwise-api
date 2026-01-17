# test_db.py
from app.core.database import Base, engine, SessionLocal
from app.models import Class, Student

# 1. 创建表
Base.metadata.create_all(bind=engine)
print("✅ 表结构已创建")

# 2. 插入测试数据
db = SessionLocal()
try:
    # 检查是否已有数据（避免重复插入）
    if db.query(Class).count() == 0:
        cls = Class(name="高一(3)班")
        db.add(cls)
        db.commit()
        db.refresh(cls)

        student = Student(name="张三", gender="男", class_id=cls.id)
        db.add(student)
        db.commit()
        print("✅ 测试数据已插入")
    else:
        print("ℹ️ 数据已存在，跳过插入")
finally:
    db.close()