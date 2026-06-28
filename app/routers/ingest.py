"""Data ingestion endpoints — JSON, CSV, Excel, and webhooks."""
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RawData, IngestStatus
from app.schemas import IngestResponse, JobStatusResponse
from app.services.csv_parser import parse_csv, count_csv_rows
from app.services.excel_parser import parse_excel, count_excel_rows
from app.etl.pipeline import ETLPipeline

log = logging.getLogger(__name__)
router = APIRouter()

# In-memory job tracking (replace with Celery/Redis in production)
_jobs: dict[str, dict[str, Any]] = {}


def _submit_job(source: str, payload: Any, file_name: str | None = None) -> str:
    job_id = str(uuid.uuid4())[:8]
    raw = RawData(source=source, payload=payload, file_name=file_name, status=IngestStatus.PENDING.value)
    db = next(get_db())
    db.add(raw)
    db.commit()
    db.refresh(raw)
    _jobs[job_id] = {
        "job_id": raw.id,
        "status": IngestStatus.PENDING.value,
        "rows_processed": 0,
        "rows_failed": 0,
        "started_at": raw.ingested_at,
        "finished_at": None,
        "error_message": None,
    }
    # Update status to running
    raw.status = IngestStatus.RUNNING.value
    db.commit()
    _jobs[job_id]["status"] = IngestStatus.RUNNING.value
    return job_id


@router.post("/ingest/json", response_model=IngestResponse)
async def ingest_json(payload: dict, db: Session = Depends(get_db)):
    """Accept arbitrary JSON payload and store in raw_data."""
    source = "json_api"
    job_id = _submit_job(source, payload)
    # Process synchronously for JSON (small payloads)
    raw = db.query(RawData).filter(RawData.id == _jobs[job_id]["job_id"]).first()
    raw.status = IngestStatus.DONE.value
    db.commit()
    _jobs[job_id]["status"] = IngestStatus.DONE.value
    _jobs[job_id]["rows_processed"] = 1
    _jobs[job_id]["finished_at"] = datetime.utcnow()
    log.info(f"JSON ingest job {job_id}: 1 row stored")
    return IngestResponse(job_id=job_id, status="done", message="1 row stored")


@router.post("/ingest/csv", response_model=IngestResponse)
async def ingest_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Accept CSV file upload, parse, and load to staging."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Must be a .csv file")
    content = await file.read()
    try:
        rows = list(parse_csv(content))
        row_count = len(rows)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV parse error: {e}")
    if not rows:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    job_id = _submit_job("csv_upload", rows, file.filename)
    raw = db.query(RawData).filter(RawData.id == _jobs[job_id]["job_id"]).first()
    # Run ETL pipeline
    pipeline = ETLPipeline(pipeline_name=f"csv_ingest_{job_id}", db=db)
    processed, failed = pipeline.run("raw_data", "processed_data", rows)
    raw.status = IngestStatus.DONE.value
    db.commit()
    _jobs[job_id]["status"] = IngestStatus.DONE.value
    _jobs[job_id]["rows_processed"] = processed
    _jobs[job_id]["rows_failed"] = failed
    _jobs[job_id]["finished_at"] = datetime.utcnow()
    log.info(f"CSV ingest job {job_id}: {processed} processed, {failed} failed")
    return IngestResponse(job_id=job_id, status="done", message=f"{processed} rows loaded")


@router.post("/ingest/excel", response_model=IngestResponse)
async def ingest_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Accept .xlsx file upload, parse all sheets, and load to staging."""
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Must be an .xlsx or .xls file")
    content = await file.read()
    try:
        rows = list(parse_excel(content))
        row_count = len(rows)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Excel parse error: {e}")
    if not rows:
        raise HTTPException(status_code=400, detail="Excel file has no data")
    job_id = _submit_job("excel_upload", rows, file.filename)
    raw = db.query(RawData).filter(RawData.id == _jobs[job_id]["job_id"]).first()
    # Run ETL pipeline
    pipeline = ETLPipeline(pipeline_name=f"excel_ingest_{job_id}", db=db)
    processed, failed = pipeline.run("raw_data", "processed_data", rows)
    raw.status = IngestStatus.DONE.value
    db.commit()
    _jobs[job_id]["status"] = IngestStatus.DONE.value
    _jobs[job_id]["rows_processed"] = processed
    _jobs[job_id]["rows_failed"] = failed
    _jobs[job_id]["finished_at"] = datetime.utcnow()
    log.info(f"Excel ingest job {job_id}: {processed} processed, {failed} failed")
    return IngestResponse(job_id=job_id, status="done", message=f"{processed} rows loaded from {len(set(r.get('_sheet') for r in rows))} sheets")


@router.post("/ingest/webhook/{source}", response_model=IngestResponse)
async def ingest_webhook(source: str, payload: dict, db: Session = Depends(get_db)):
    """Receive webhook payloads from external services."""
    job_id = _submit_job(f"webhook_{source}", payload)
    raw = db.query(RawData).filter(RawData.id == _jobs[job_id]["job_id"]).first()
    raw.status = IngestStatus.DONE.value
    db.commit()
    _jobs[job_id]["status"] = IngestStatus.DONE.value
    _jobs[job_id]["rows_processed"] = 1
    _jobs[job_id]["finished_at"] = datetime.utcnow()
    log.info(f"Webhook ingest job {job_id} from source {source}")
    return IngestResponse(job_id=job_id, status="done", message="webhook received")


@router.get("/ingest/status/{job_id}", response_model=JobStatusResponse)
async def ingest_status(job_id: str, db: Session = Depends(get_db)):
    """Check ETL job status by job_id."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    job = _jobs[job_id]
    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        rows_processed=job["rows_processed"],
        rows_failed=job["rows_failed"],
        started_at=job["started_at"],
        finished_at=job["finished_at"],
        error_message=job["error_message"],
    )