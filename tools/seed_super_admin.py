#!/usr/bin/env python3
"""
Run once to create the first super_admin:
  python tools/seed_super_admin.py --phone 13800000000 --password AdminPass123 --name "校管理员"
"""
import sys
import argparse

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, ".")

from app.core.database import Base, engine
from app.db.session import SessionLocal
from app.models.teacher import Teacher
from app.core.security import hash_password

Base.metadata.create_all(bind=engine)

parser = argparse.ArgumentParser()
parser.add_argument("--phone", required=True)
parser.add_argument("--password", required=True)
parser.add_argument("--name", required=True)
args = parser.parse_args()

db = SessionLocal()
if db.query(Teacher).filter(Teacher.role == "super_admin").first():
    print("超级管理员已存在，跳过")
    db.close()
    sys.exit(0)

t = Teacher(phone=args.phone, hashed_password=hash_password(args.password), name=args.name, role="super_admin")
db.add(t)
db.commit()
print(f"超级管理员创建成功: {args.name} ({args.phone})")
db.close()
