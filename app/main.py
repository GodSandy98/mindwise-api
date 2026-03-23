from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine
from app.api.v1.endpoints import health, students, score, reports, exams, answers, classes, indicators, auth, teachers

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MindWise API",
    description="Student psychological assessment backend",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(students.router, prefix="/api/v1")
app.include_router(score.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(exams.router, prefix="/api/v1")
app.include_router(answers.router, prefix="/api/v1")
app.include_router(classes.router, prefix="/api/v1")
app.include_router(indicators.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(teachers.router, prefix="/api/v1")
