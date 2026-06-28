"""Data query API — paginated access to processed tables."""
import csv
import io
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ProcessedData

router = APIRouter()


@router.get("/data/{table}")
async def query_table(
    table: str,
    limit: int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    data_type: str | None = None,
    db: Session = Depends(get_db),
):
    """Query any processed table with pagination."""
    # Whitelist allowed tables to prevent SQL injection
    allowed = {"processed_data", "raw_data", "pipeline_runs", "transformation_rules"}
    if table not in allowed:
        raise HTTPException(status_code=400, detail="Table not allowed")

    model_map = {
        "processed_data": ProcessedData,
    }
    model = model_map.get(table)
    if model is None:
        raise HTTPException(status_code=400, detail=f"Table {table} not queryable via this endpoint")

    q = db.query(model)
    if data_type:
        q = q.filter(model.data_type == data_type)

    total = q.count()
    rows = q.offset(offset).limit(limit).all()

    return {
        "table": table,
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": [
            {
                "id": r.id,
                "data_type": r.data_type,
                "external_id": r.external_id,
                "payload": r.payload,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        ],
    }


@router.get("/data/{table}/export")
async def export_table(
    table: str,
    format: str = Query("json", pattern="^(json|csv)$"),
    data_type: str | None = None,
    db: Session = Depends(get_db),
):
    """Export table data as JSON or CSV."""
    if table != "processed_data":
        raise HTTPException(status_code=400, detail="Only processed_data export supported")
    q = db.query(ProcessedData)
    if data_type:
        q = q.filter(ProcessedData.data_type == data_type)
    rows = q.all()

    if format == "csv":
        output = io.StringIO()
        if rows:
            fieldnames = ["id", "data_type", "external_id", "payload", "created_at", "updated_at"]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow({
                    "id": r.id,
                    "data_type": r.data_type,
                    "external_id": r.external_id or "",
                    "payload": str(r.payload),
                    "created_at": r.created_at.isoformat() if r.created_at else "",
                    "updated_at": r.updated_at.isoformat() if r.updated_at else "",
                })
        return StreamingResponse(
            [output.getvalue()],
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={table}.csv"},
        )

    # JSON
    return {
        "table": table,
        "count": len(rows),
        "data": [
            {
                "id": r.id,
                "data_type": r.data_type,
                "external_id": r.external_id,
                "payload": r.payload,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        ],
    }


@router.get("/data/{table}/aggregate")
async def aggregate_table(
    table: str,
    group_by: str = Query(...),
    agg_func: str = Query("count", pattern="^(count|sum|avg)$"),
    field: str = Query("id"),
    data_type: str | None = None,
    db: Session = Depends(get_db),
):
    """Simple aggregation on processed_data."""
    if table != "processed_data":
        raise HTTPException(status_code=400, detail="Only processed_data aggregate supported")

    q = db.query(ProcessedData)
    if data_type:
        q = q.filter(ProcessedData.data_type == data_type)

    if agg_func == "count":
        result = db.query(
            getattr(ProcessedData, group_by).label("key"),
            func.count(ProcessedData.id).label("value")
        ).group_by(getattr(ProcessedData, group_by)).all()
    elif agg_func == "sum":
        result = db.query(
            getattr(ProcessedData, group_by).label("key"),
            func.sum(getattr(ProcessedData, field)).label("value")
        ).group_by(getattr(ProcessedData, group_by)).all()
    elif agg_func == "avg":
        result = db.query(
            getattr(ProcessedData, group_by).label("key"),
            func.avg(getattr(ProcessedData, field)).label("value")
        ).group_by(getattr(ProcessedData, group_by)).all()

    return {
        "table": table,
        "group_by": group_by,
        "agg": agg_func,
        "data": [{"key": str(k), "value": float(v) if v is not None else 0} for k, v in result],
    }