"""Health check endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import HealthResponse, PipelineHealthResponse

router = APIRouter()

@router.get("/health/", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    return HealthResponse(status="ok", database=db_status)

@router.get("/health/pipeline", response_model=PipelineHealthResponse)
async def pipeline_health(db: Session = Depends(get_db)):
    from app.models import PipelineRun
    total = db.query(PipelineRun).count()
    if total == 0:
        return PipelineHealthResponse(total_runs=0, success_rate=1.0, last_run=None)
    done = db.query(PipelineRun).filter(PipelineRun.status == "done").count()
    last = db.query(PipelineRun).order_by(PipelineRun.started_at.desc()).first()
    return PipelineHealthResponse(
        total_runs=total,
        success_rate=round(done/total, 3),
        last_run=last.started_at if last else None
    )