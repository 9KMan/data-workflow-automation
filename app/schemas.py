"""Pydantic schemas for data automation platform."""
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class IngestPayload(BaseModel):
    """Payload for data ingestion."""
    source: str
    payload: dict


class IngestResponse(BaseModel):
    """Response from ingestion endpoint."""
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    """Status response for a job."""
    job_id: int
    status: str
    rows_processed: int
    rows_failed: int
    started_at: datetime
    finished_at: datetime | None = None
    error_message: str | None = None


class DataQueryParams(BaseModel):
    """Query parameters for data retrieval."""
    limit: int = 100
    offset: int = 0
    data_type: str | None = None


class AggregateParams(BaseModel):
    """Parameters for aggregation queries."""
    group_by: str
    agg_func: Annotated[str, Field(pattern="^(count|sum|avg)$")]
    field: str


class TriggerPayload(BaseModel):
    """Payload to trigger a pipeline or event."""
    event: str
    data: dict
    pipeline_name: str | None = None


class N8NWebhookPayload(BaseModel):
    """Payload for n8n webhook integration."""
    url: str
    payload: dict


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    database: str


class PipelineHealthResponse(BaseModel):
    """Pipeline health metrics."""
    total_runs: int
    success_rate: float
    last_run: datetime | None = None