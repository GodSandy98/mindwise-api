# test_db.py
from app.core.database import engine
from app.core.database import Base
Base.metadata.create_all(engine)
print("Tables created successfully!")