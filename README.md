# Data & Workflow Automation Platform

> ETL pipelines, data ingestion, and n8n workflow automation — in production in ~5 minutes.

**Built by: KMan | AI-Augmented Engineering Factory**

---

## Quick Start

```bash
# 1. Clone and enter
git clone <repo> && cd <repo>

# 2. Configure environment
cp .env.example .env
# Edit .env — set API_KEY, DATABASE_URL, N8N_WEBHOOK_URL

# 3. Start everything (app + PostgreSQL)
docker compose up --build

# 4. Verify
curl http://localhost:8000/api/v1/health/
# → {"status":"ok","database":"connected"}
```

---

## Architecture

```
                              ┌─────────────────────┐
                              │   External Sources   │
                              │  (CSV, Excel, JSON,  │
                              │   Webhooks, REST)    │
                              └─────────┬───────────┘
                                        │ POST /api/v1/ingest/*
                                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data & Workflow Automation API              │
│                     FastAPI + SQLAlchemy                      │
│  ┌──────────┐  ┌───────────┐  ┌───────────┐  ┌─────────┐  │
│  │  Ingest  │  │    ETL    │  │   Data    │  │Automate │  │
│  │  Router  │──│ Pipeline  │──│   Router  │  │ Router  │  │
│  └──────────┘  └─────┬─────┘  └───────────┘  └────┬────┘  │
│                       │                              │        │
│              ┌────────▼────────┐         ┌──────────▼──────┐ │
│              │ Transformation │         │  n8n Webhook    │ │
│              │     Rules      │         │     Client      │ │
│              └────────────────┘         └──────────┬──────┘ │
└──────────────────────────────────────────────────────────────┘
                                        │ POST /api/v1/automate/*
                                        ▼
                              ┌─────────────────────┐
                              │   n8n Workflows     │
                              │  (Email, Slack,     │
                              │   CRM integrations)  │
                              └─────────────────────┘
                                        │
                              ┌─────────▼───────────┐
                              │    PostgreSQL DB      │
                              │ raw_data / processed_ │
                              │ data / pipeline_runs  │
                              └──────────────────────┘
```

---

## Data Sources & Integrations

| Source | Method | Endpoint | Status |
|---|---|---|---|
| CSV file upload | `multipart/form-data` | `POST /api/v1/ingest/csv` | ✅ Ready |
| Excel `.xlsx` upload | `multipart/form-data` | `POST /api/v1/ingest/excel` | ✅ Ready |
| Arbitrary JSON | JSON body | `POST /api/v1/ingest/json` | ✅ Ready |
| Webhooks (Stripe, Slack, etc.) | HTTP POST | `POST /api/v1/ingest/webhook/{source}` | ✅ Ready |
| n8n automation triggers | HTTP POST | `POST /api/v1/automate/n8n-webhook` | ✅ Ready |
| Direct data query | URL params | `GET /api/v1/data/{table}` | ✅ Ready |

---

## Database Schema

### `raw_data`
Ingested data in original form.

| Column | Type | Description |
|---|---|---|
| `id` | SERIAL PK | Auto-increment ID |
| `source` | VARCHAR(100) | Source identifier (e.g. `csv_upload`, `webhook_stripe`) |
| `ingested_at` | TIMESTAMP | Ingestion timestamp |
| `payload` | JSON | Raw data as received |
| `file_name` | VARCHAR(255) | Original file name (file uploads) |
| `status` | VARCHAR(20) | `pending` / `running` / `done` / `failed` |

### `transformation_rules`
Configurable ETL rules — no code changes needed to add new transformations.

| Column | Type | Description |
|---|---|---|
| `id` | SERIAL PK | Auto-increment ID |
| `source_table` | VARCHAR(100) | Table/stream this rule applies to |
| `target_table` | VARCHAR(100) | Where transformed data goes |
| `field_name` | VARCHAR(255) | Field this rule operates on |
| `transform_type` | VARCHAR(50) | `coerce` / `default` / `map` / `drop` / `custom` |
| `transform_config` | JSON | Config for the transform |

**Transform types:**

| Type | Description | Example Config |
|---|---|---|
| `coerce` | Type conversion | `{"type": "float", "default": 0.0}` |
| `default` | Fill nulls | `{"default": "unknown"}` |
| `map` | Value lookup | `{"map": {"old": "new"}}` |
| `drop` | Remove field | `{}` |
| `custom` | Registered Python function | `{"fn": "my_transform"}` |

### `pipeline_runs`
Every ETL execution logged.

| Column | Type | Description |
|---|---|---|
| `id` | SERIAL PK | Auto-increment ID |
| `pipeline_name` | VARCHAR(100) | Name of the pipeline |
| `status` | VARCHAR(20) | `running` / `done` / `failed` |
| `rows_processed` | INT | Successfully processed rows |
| `rows_failed` | INT | Failed rows |
| `started_at` | TIMESTAMP | Run start time |
| `finished_at` | TIMESTAMP | Run end time (null if running) |
| `error_message` | TEXT | Error details if failed |

### `processed_data`
Final structured data ready for querying.

| Column | Type | Description |
|---|---|---|
| `id` | SERIAL PK | Auto-increment ID |
| `data_type` | VARCHAR(100) | Domain type (e.g. `orders`, `inventory`) |
| `external_id` | VARCHAR(255) | ID from source system |
| `payload` | JSON | Transformed data record |
| `created_at` | TIMESTAMP | Record creation time |
| `updated_at` | TIMESTAMP | Last update time |

---

## CLI Reference

### Local Development

```bash
# Install dependencies
uv pip install -r requirements.txt

# Run without Docker
export DATABASE_URL="postgresql://automation:automation@localhost:5432/automation_db"
export API_KEY="your-secret-key"
export N8N_WEBHOOK_URL="http://localhost:5678/webhook/test"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
python -m pytest tests/ -v

# Run with Docker
docker compose up --build
```

### API Examples

```bash
# Health check
curl http://localhost:8000/api/v1/health/

# Ingest JSON
curl -X POST http://localhost:8000/api/v1/ingest/json \
  -H "X-API-Key: dev-api-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"order_id": "12345", "customer": "Alice", "total": 99.99}'

# Ingest CSV (replace @file.csv with actual file path)
curl -X POST http://localhost:8000/api/v1/ingest/csv \
  -H "X-API-Key: dev-api-key-change-me" \
  -F "file=@sample_data.csv"

# Ingest Excel
curl -X POST http://localhost:8000/api/v1/ingest/excel \
  -H "X-API-Key: dev-api-key-change-me" \
  -F "file=@sample_data.xlsx"

# Check job status
curl http://localhost:8000/api/v1/ingest/status/a1b2c3d4 \
  -H "X-API-Key: dev-api-key-change-me"

# Query processed data
curl "http://localhost:8000/api/v1/data/processed_data?limit=10" \
  -H "X-API-Key: dev-api-key-change-me"

# Export as CSV
curl "http://localhost:8000/api/v1/data/processed_data/export?format=csv" \
  -H "X-API-Key: dev-api-key-change-me"

# Aggregate data
curl "http://localhost:8000/api/v1/data/processed_data/aggregate?group_by=data_type&agg_func=count" \
  -H "X-API-Key: dev-api-key-change-me"

# Trigger n8n automation
curl -X POST http://localhost:8000/api/v1/automate/n8n-webhook \
  -H "X-API-Key: dev-api-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://n8n.example.com/webhook/my-workflow", "payload": {"order_id": "12345"}}'
```

---

## Quality Guarantees

| Concern | Guarantee |
|---|---|
| **Reliability** | ETL pipeline retries 3× with exponential backoff on transient failures |
| **Data integrity** | Transformation rules applied atomically per row; failed rows logged with error details |
| **Observability** | Every pipeline run logged to `pipeline_runs` with row counts, timing, and error messages |
| **Health** | `GET /api/v1/health/` returns DB connectivity status; `GET /api/v1/health/pipeline` returns pipeline statistics |
| **Security** | API key required on all endpoints; no secrets in code; input validation on all uploads |
| **Portability** | Single `docker compose up` brings up app + PostgreSQL; no external services required |
| **Testability** | 25 pytest tests covering ETL transforms, parsers, pipeline logic, and API endpoints |
| **Production-ready** | Structured JSON logging; CORS enabled; graceful startup/shutdown |

---

## n8n Integration

Connect n8n workflows to `/api/v1/automate/n8n-webhook` for:

- **Email on pipeline failure** — n8n reads webhook payload → sends email alert
- **Slack notifications** — n8n posts to Slack channel when data threshold exceeded
- **CRM auto-tagging** — n8n reads new record → tags in HubSpot/Salesforce

```
n8n Workflow:
  [Webhook Node] → [Switch/IF] → [Email / Slack / CRM]
                         ↑
  POST /api/v1/automate/n8n-webhook
  Body: { "url": "...", "payload": {...} }
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `API_KEY` | `dev-api-key-change-me` | API key for all endpoints |
| `DATABASE_URL` | `postgresql://...` | PostgreSQL connection string |
| `N8N_WEBHOOK_URL` | `http://localhost:5678/webhook/test` | Default n8n webhook URL |
| `ETL_MAX_RETRIES` | `3` | Max ETL retry attempts |
| `ETL_BATCH_SIZE` | `1000` | Rows processed per batch |

---

## Project Structure

```
<project>/
├── SPEC.md                    ← Full specification
├── README.md                  ← This file
├── .env.example               ← Required env vars
├── Dockerfile                 ← App container
├── docker-compose.yml         ← App + PostgreSQL
├── requirements.txt           ← Python deps
├── pytest.ini                 ← Test configuration
├── app/
│   ├── main.py                ← FastAPI entry point
│   ├── config.py              ← Environment config
│   ├── database.py            ← SQLAlchemy engine + session
│   ├── models.py              ← ORM models
│   ├── schemas.py             ← Pydantic request/response schemas
│   ├── routers/
│   │   ├── ingest.py          ← POST /api/v1/ingest/*
│   │   ├── data.py            ← GET /api/v1/data/*
│   │   ├── automate.py        ← POST /api/v1/automate/*
│   │   └── health.py          ← GET /api/v1/health/*
│   ├── etl/
│   │   ├── pipeline.py        ← ETL orchestration
│   │   ├── transformers.py    ← Built-in transform functions
│   │   └── registry.py        ← Custom transform registry
│   └── services/
│       ├── csv_parser.py      ← CSV ingestion
│       ├── excel_parser.py    ← Excel ingestion
│       └── n8n_client.py      ← n8n webhook caller
├── tests/
│   ├── conftest.py            ← Pytest fixtures
│   ├── test_health.py         ← Health endpoint tests
│   ├── test_parsers.py        ← CSV/Excel parser tests
│   ├── test_pipeline.py       ← ETL pipeline tests
│   └── test_transformers.py  ← Transform function tests
└── docs/
    ├── data-model.md           ← Database schema details
    └── api-reference.md        ← Full API reference
```