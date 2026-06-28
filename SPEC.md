# SPEC — Data & Workflow Automation Platform

## 1. Background

A small/mid-sized business needs to automate their data workflows so information moves cleanly from collection to action without manual work. The focus is practical implementation — not theory — with strong attention to reliability and clarity of data flow.

**Core problem:** Manual data entry and transfer between forms, APIs, spreadsheets, and databases is error-prone and time-consuming. A single source of truth is needed.

**Core solution:** A Python-powered data automation platform that:
- Pulls data from REST APIs, databases (PostgreSQL), and Excel/CSV files
- Transforms and structures data through ETL pipelines
- Exposes data via REST API for dashboards and downstream consumers
- Triggers automated actions via n8n workflows

## 2. Goals & Non-goals

**In scope**
- REST API for data ingestion from external sources (webhooks, manual upload)
- Python ETL pipeline: extract → transform → load with configurable rules
- PostgreSQL data warehouse: structured storage with queryable API
- Excel/CSV import: upload via API or file, parse, validate, load
- n8n workflow integration: trigger n8n webhooks on data events
- Dashboard-ready data outputs (JSON API with filters)
- Dockerized for local development and production

**Out of scope**
- Frontend dashboard UI (data served via API only)
- Native mobile app
- OAuth / multi-user auth (single API key for now)
- Real-time streaming (batch ETL is sufficient for <30hr/week workloads)

## 3. Functional Requirements

### 3.1 Data Ingestion API

- `POST /api/v1/ingest/json` — Accept arbitrary JSON payload, validate schema, store in raw table
- `POST /api/v1/ingest/csv` — Accept CSV file upload, parse, validate headers, load to staging table
- `POST /api/v1/ingest/excel` — Accept .xlsx upload via multipart/form-data, parse all sheets, load to staging
- `POST /api/v1/ingest/webhook/{source}` — Receive webhook payloads from external services (Slack, Stripe, etc.)
- `GET /api/v1/ingest/status/{job_id}` — Check ETL job status (pending/running/done/failed)

### 3.2 ETL Pipeline

- Configurable transformation rules stored in DB (no code changes for new rules)
- Built-in transformations: type coercion, date parsing, currency normalization, null handling
- Custom transformation hooks: define Python functions registered via API
- Pipeline execution: synchronous (fast) or background (Celery-style via threading)
- Retry logic: 3 attempts with exponential backoff on transient failures
- Pipeline runs logged to `pipeline_runs` table with row counts and error details

### 3.3 Data Storage

- `raw_data` table: stores all ingested data with source, timestamp, raw payload
- `staging_data` table: post-transformation data before final load
- `processed_data` table: final structured data ready for querying
- `transformation_rules` table: configurable ETL rules (field mapping, type, defaults)
- `pipeline_runs` table: execution log with stats

### 3.4 Data Query API

- `GET /api/v1/data/{table}` — Query any processed table with pagination (limit, offset)
- `GET /api/v1/data/{table}/export` — Export to CSV or JSON
- `GET /api/v1/data/{table}/aggregate` — Simple aggregation: count, sum, avg by group
- `GET /api/v1/data/{table}/filter` — Filter by field values (URL query params)

### 3.5 Automation Triggers (n8n Integration)

- `POST /api/v1/automate/trigger` — Internal: called by ETL pipeline on data events
- `POST /api/v1/automate/n8n-webhook` — Forward data to n8n webhook URL (configurable per pipeline)
- Built-in trigger conditions: new data, data changed, threshold exceeded, scheduled

### 3.6 Health & Monitoring

- `GET /api/v1/health/` — Returns `{ "status": "ok", "database": "connected" }` with live DB check
- `GET /api/v1/health/pipeline` — Returns pipeline stats: total runs, success rate, last run time

## 4. Data Model

### Tables

```sql
-- raw data ingestion log
CREATE TABLE raw_data (
    id SERIAL PRIMARY KEY,
    source VARCHAR(100) NOT NULL,
    ingested_at TIMESTAMP DEFAULT NOW(),
    payload JSONB NOT NULL,
    file_name VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending'
);

-- transformation rules
CREATE TABLE transformation_rules (
    id SERIAL PRIMARY KEY,
    source_table VARCHAR(100) NOT NULL,
    target_table VARCHAR(100) NOT NULL,
    field_name VARCHAR(255) NOT NULL,
    transform_type VARCHAR(50) NOT NULL, -- 'coerce', 'default', 'map', 'drop', 'custom'
    transform_config JSONB, -- {'type': 'float', 'default': 0} or {'map': {'old': 'new'}}
    created_at TIMESTAMP DEFAULT NOW()
);

-- pipeline execution log
CREATE TABLE pipeline_runs (
    id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'running', 'done', 'failed'
    rows_processed INT DEFAULT 0,
    rows_failed INT DEFAULT 0,
    started_at TIMESTAMP DEFAULT NOW(),
    finished_at TIMESTAMP,
    error_message TEXT
);

-- processed data (per domain: orders, inventory, customers, etc.)
CREATE TABLE processed_data (
    id SERIAL PRIMARY KEY,
    data_type VARCHAR(100) NOT NULL,
    external_id VARCHAR(255),
    payload JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 5. Non-functional Requirements

| Concern | Requirement |
|---|---|
| Performance | p95 < 500ms for single-row API ops; ETL batch of 10K rows < 30s |
| Reliability | ETL pipeline retries 3x; dead-letter queue for failed rows |
| Security | API key authentication; no secrets in code; input validation on all endpoints |
| Observability | Structured JSON logging; health endpoints; pipeline run stats |
| Portability | `docker compose up` starts everything; no external services required |
| Testability | ≥10 pytest tests covering ETL transforms, API endpoints, data validation |

## 6. Acceptance Criteria

- `docker compose up` starts app + Postgres; `GET /api/v1/health/` returns `{"status": "ok", ...}`
- CSV upload via `POST /api/v1/ingest/csv` parses and stores data correctly
- Excel upload via `POST /api/v1/ingest/excel` parses multi-sheet .xlsx and loads all rows
- ETL pipeline applies transformation rules from DB and logs execution to `pipeline_runs`
- `GET /api/v1/data/processed_data` returns paginated processed data as JSON
- n8n webhook trigger fires when ETL pipeline completes (configurable URL)
- `GET /api/v1/ingest/status/{job_id}` returns correct job status
- `pytest` passes locally without external services (uses in-memory SQLite where possible)
- All secrets come from environment variables; `.env.example` documents them

## 7. n8n Workflow Reference

The n8n workflow connects to `POST /api/v1/automate/n8n-webhook` and handles:
- Email notifications on pipeline failure
- Slack alerts when data threshold exceeded
- Auto-tagging records in downstream systems

## 8. Project Structure

```
JOB-20260628150000-000117/
├── SPEC.md                    ← this file
├── README.md                  ← setup, architecture, CLI reference, quality guarantees
├── .env.example               ← required env vars
├── Dockerfile                 ← app container
├── docker-compose.yml         ← app + postgres
├── requirements.txt           ← Python deps
├── app/
│   ├── __init__.py
│   ├── main.py                ← FastAPI app entry point
│   ├── config.py              ← env var loading
│   ├── models.py              ← SQLAlchemy models
│   ├── schemas.py             ← Pydantic schemas
│   ├── database.py            ← DB connection
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── ingest.py          ← POST /api/v1/ingest/*
│   │   ├── data.py            ← GET /api/v1/data/*
│   │   ├── automate.py        ← POST /api/v1/automate/*
│   │   └── health.py          ← GET /api/v1/health/*
│   ├── etl/
│   │   ├── __init__.py
│   │   ├── pipeline.py        ← ETL orchestration
│   │   ├── transformers.py    ← built-in transform functions
│   │   └── registry.py        ← custom transform hook registry
│   └── services/
│       ├── __init__.py
│       ├── csv_parser.py      ← CSV ingestion
│       ├── excel_parser.py    ← Excel ingestion
│       └── n8n_client.py      ← n8n webhook caller
├── tests/
│   ├── __init__.py
│   ├── test_ingest.py
│   ├── test_etl.py
│   ├── test_data_api.py
│   └── test_health.py
└── docs/
    ├── data-model.md
    └── api-reference.md
```