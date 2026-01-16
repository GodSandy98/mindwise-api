from fastapi import FastAPI
from app.api.v1.endpoints import health

app = FastAPI(
    title="MindWise API",
    description="Student psychological assessment backend",
    version="0.1.0",
)

app.include_router(health.router, prefix="/api/v1")