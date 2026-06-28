# API Reference

Base URL: `http://localhost:8000/api/v1`

## Authentication

All endpoints require `X-API-Key` header:
```
X-API-Key: your-api-key
```

## Ingest

### `POST /api/v1/ingest/json`

Ingest arbitrary JSON payload.

**Request body:**
```json
{
  "order_id": "12345",
  "customer": "Alice",
  "total": 99.99,
  "items": ["Widget A", "Widget B"]
}
```

**Response:**
```json
{
  "job_id": "a1b2c3d4",
  "status": "done",
  "message": "1 row stored"
}
```

---

### `POST /api/v1/ingest/csv`

Upload and ingest a CSV file.

**Request:** `multipart/form-data`
- `file`: CSV file

**Response:**
```json
{
  "job_id": "b2c3d4e5",
  "status": "done",
  "message": "150 rows loaded"
}
```

**Errors:**
- `400` — File is not `.csv`
- `400` — CSV parse error
- `400` — Empty file

---

### `POST /api/v1/ingest/excel`

Upload and ingest an Excel `.xlsx` file (multi-sheet supported).

**Request:** `multipart/form-data`
- `file`: `.xlsx` file

**Response:**
```json
{
  "job_id": "c3d4e5f6",
  "status": "done",
  "message": "320 rows loaded from 3 sheets"
}
```

**Errors:**
- `400` — File is not `.xlsx` or `.xls`
- `400` — Excel parse error
- `400` — No data in file

---

### `POST /api/v1/ingest/webhook/{source}`

Receive webhook payloads from external services.

**Path params:**
- `source`: identifier for the webhook source (e.g. `stripe`, `slack`)

**Request body:** Any JSON

**Response:**
```json
{
  "job_id": "d4e5f6g7",
  "status": "done",
  "message": "webhook received"
}
```

---

### `GET /api/v1/ingest/status/{job_id}`

Check the status of an ingestion job.

**Response:**
```json
{
  "job_id": 42,
  "status": "done",
  "rows_processed": 150,
  "rows_failed": 0,
  "started_at": "2024-06-15T10:00:00",
  "finished_at": "2024-06-15T10:00:03",
  "error_message": null
}
```

**Status values:** `pending` | `running` | `done` | `failed`

---

## Data

### `GET /api/v1/data/{table}`

Query processed data with pagination.

**Path params:**
- `table`: Table name (`processed_data`, `raw_data`, `pipeline_runs`, `transformation_rules`)

**Query params:**
- `limit` (int, default 100, max 10000)
- `offset` (int, default 0)
- `data_type` (string, optional) — filter by data type

**Response:**
```json
{
  "table": "processed_data",
  "total": 320,
  "limit": 100,
  "offset": 0,
  "data": [
    {
      "id": 1,
      "data_type": "orders",
      "external_id": "12345",
      "payload": { "customer": "Alice", "total": 99.99 },
      "created_at": "2024-06-15T10:00:00",
      "updated_at": "2024-06-15T10:00:00"
    }
  ]
}
```

---

### `GET /api/v1/data/{table}/export`

Export processed data as CSV or JSON.

**Query params:**
- `format`: `json` (default) or `csv`
- `data_type` (optional): filter by data type

**Response:** File download

---

### `GET /api/v1/data/{table}/aggregate`

Simple aggregation on processed data.

**Query params:**
- `group_by`: field to group by (e.g. `data_type`)
- `agg_func`: `count` (default), `sum`, `avg`
- `field`: numeric field for sum/avg (e.g. `id`)
- `data_type` (optional): filter by data type

**Response:**
```json
{
  "table": "processed_data",
  "group_by": "data_type",
  "agg": "count",
  "data": [
    { "key": "orders", "value": 150 },
    { "key": "inventory", "value": 80 }
  ]
}
```

---

## Automation

### `POST /api/v1/automate/trigger`

Internal automation trigger — called by ETL pipeline on data events.

**Request body:**
```json
{
  "event": "pipeline_done",
  "data": { "pipeline": "orders_etl", "rows": 150 },
  "pipeline_name": "orders_etl"
}
```

**Response:**
```json
{
  "event": "pipeline_done",
  "triggered": true,
  "pipeline": "orders_etl"
}
```

---

### `POST /api/v1/automate/n8n-webhook`

Forward data to a specific n8n webhook URL.

**Request body:**
```json
{
  "url": "https://n8n.example.com/webhook/my-workflow",
  "payload": { "order_id": "12345", "total": 99.99 }
}
```

**Response:**
```json
{
  "status": "ok",
  "url": "https://n8n.example.com/webhook/my-workflow"
}
```

---

## Health

### `GET /api/v1/health/`

Basic health check.

**Response:**
```json
{
  "status": "ok",
  "database": "connected"
}
```

---

### `GET /api/v1/health/pipeline`

Pipeline execution statistics.

**Response:**
```json
{
  "total_runs": 47,
  "success_rate": 0.957,
  "last_run": "2024-06-15T10:00:00"
}
```

---

## n8n Integration Example

Connect n8n workflow to `/api/v1/automate/n8n-webhook` for:

- **Email on pipeline failure:** n8n reads webhook payload → sends email
- **Slack alert on threshold:** n8n checks `data.threshold_exceeded` → posts to Slack
- **Auto-tagging:** n8n reads new record → updates CRM

```
n8n Workflow:
  [Webhook Node] → [Switch Node] → [Email/Slack/CRM]
                         ↑
  POST /api/v1/automate/trigger
  sends event="new_data" payload={...}
```