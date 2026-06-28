"""SQLAlchemy ORM models for the data automation platform."""
import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Enum as SQLEnum,
    JSON, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database import Base


class IngestStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class PipelineStatus(str, enum.Enum):
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class RawData(Base):
    __tablename__ = "raw_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(100), nullable=False)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    payload = Column(JSON, nullable=False)  # JSONB on postgres
    file_name = Column(String(255), nullable=True)
    status = Column(String(20), default=IngestStatus.PENDING.value)


class TransformationRule(Base):
    __tablename__ = "transformation_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_table = Column(String(100), nullable=False)
    target_table = Column(String(100), nullable=False)
    field_name = Column(String(255), nullable=False)
    transform_type = Column(String(50), nullable=False)  # coerce, default, map, drop, custom
    transform_config = Column(JSON, nullable=True)  # {'type': 'float', 'default': 0}
    created_at = Column(DateTime, default=datetime.utcnow)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pipeline_name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)
    rows_processed = Column(Integer, default=0)
    rows_failed = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)


class ProcessedData(Base):
    __tablename__ = "processed_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_type = Column(String(100), nullable=False)
    external_id = Column(String(255), nullable=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_processed_data_data_type", "data_type"),
        Index("ix_processed_data_external_id", "external_id"),
    )