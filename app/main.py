"""Data & Workflow Automation Platform — FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routers import ingest, data, automate, health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting Data Automation Platform...")
    Base.metadata.create_all(bind=engine)
    log.info("Database tables created/verified.")
    yield
    log.info("Shutting down Data Automation Platform...")


app = FastAPI(
    title="Data & Workflow Automation Platform",
    description="ETL pipelines, data ingestion, and n8n workflow automation",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(ingest.router, prefix="/api/v1", tags=["ingest"])
app.include_router(data.router, prefix="/api/v1", tags=["data"])
app.include_router(automate.router, prefix="/api/v1", tags=["automate"])


@app.get("/")
async def root():
    return {"service": "Data & Workflow Automation Platform", "version": "1.0.0"}