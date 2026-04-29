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


@app.on_event("startup")
def _migrate_columns():
    """Add new columns to existing tables if they don't exist yet."""
    import sqlalchemy as _sa
    with engine.connect() as conn:
        # batch_jobs.student_ids
        batch_cols = [r[1] for r in conn.execute(_sa.text("PRAGMA table_info(batch_jobs)"))]
        if "student_ids" not in batch_cols:
            conn.execute(_sa.text("ALTER TABLE batch_jobs ADD COLUMN student_ids TEXT"))
        # exams.scores_computed_at
        exam_cols = [r[1] for r in conn.execute(_sa.text("PRAGMA table_info(exams)"))]
        if "scores_computed_at" not in exam_cols:
            conn.execute(_sa.text("ALTER TABLE exams ADD COLUMN scores_computed_at DATETIME"))
        # reports.created_at / updated_at
        report_cols = [r[1] for r in conn.execute(_sa.text("PRAGMA table_info(reports)"))]
        if "created_at" not in report_cols:
            conn.execute(_sa.text("ALTER TABLE reports ADD COLUMN created_at DATETIME"))
        if "updated_at" not in report_cols:
            conn.execute(_sa.text("ALTER TABLE reports ADD COLUMN updated_at DATETIME"))
        conn.commit()


@app.on_event("startup")
def _reset_stuck_jobs():
    """Mark any pending/running batch jobs as failed on startup.
    These jobs were killed when the server last shut down."""
    import json
    from app.db.session import SessionLocal
    from app.models.batch_job import BatchJob
    db = SessionLocal()
    try:
        stuck = db.query(BatchJob).filter(BatchJob.status.in_(["pending", "running"])).all()
        for job in stuck:
            job.status = "failed"
            existing_errors = json.loads(job.errors) if job.errors else []
            existing_errors.insert(0, {"error": "服务重启，任务中断，请重新生成"})
            job.errors = json.dumps(existing_errors, ensure_ascii=False)
        if stuck:
            db.commit()
    finally:
        db.close()

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
