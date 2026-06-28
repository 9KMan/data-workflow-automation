# Data Model

## Entity Relationship

```
raw_data
  │
  └──[ETL Pipeline]──► processed_data
                            │
transformation_rules ───────┘
  │
pipeline_runs ◄── logs ETL execution
```

## Tables

### raw_data

Stores all ingested data in its original form before transformation.

| Column | Type | Description |
|---|---|---|
| `id` | SERIAL PK | Auto-increment ID |
| `source` | VARCHAR(100) | Source system (e.g. `csv_upload`, `json_api`, `webhook_stripe`) |
| `ingested_at` | TIMESTAMP | When the data was ingested |
| `payload` | JSON | Raw data as received |
| `file_name` | VARCHAR(255) | Original file name (if file upload) |
| `status` | VARCHAR(20) | `pending` / `running` / `done` / `failed` |

### transformation_rules

Configurable ETL rules stored in the database — no code changes needed to add new transformations.

| Column | Type | Description |
|---|---|---|
| `id` | SERIAL PK | Auto-increment ID |
| `source_table` | VARCHAR(100) | Table/stream this rule applies to |
| `target_table` | VARCHAR(100) | Where transformed data goes |
| `field_name` | VARCHAR(255) | Field this rule operates on |
| `transform_type` | VARCHAR(50) | `coerce`, `default`, `map`, `drop`, `custom` |
| `transform_config` | JSON | Configuration for the transform (e.g. `{"type": "float", "default": 0}`) |
| `created_at` | TIMESTAMP | When the rule was created |

### pipeline_runs

Execution log for every ETL pipeline run.

| Column | Type | Description |
|---|---|---|
| `id` | SERIAL PK | Auto-increment ID |
| `pipeline_name` | VARCHAR(100) | Name of the pipeline that ran |
| `status` | VARCHAR(20) | `running` / `done` / `failed` |
| `rows_processed` | INT | Number of rows successfully processed |
| `rows_failed` | INT | Number of rows that failed |
| `started_at` | TIMESTAMP | When the run started |
| `finished_at` | TIMESTAMP | When the run finished (null if running) |
| `error_message` | TEXT | Error details if failed |

### processed_data

Final structured data ready for querying and downstream consumers.

| Column | Type | Description |
|---|---|---|
| `id` | SERIAL PK | Auto-increment ID |
| `data_type` | VARCHAR(100) | Domain type (e.g. `orders`, `inventory`, `customers`) |
| `external_id` | VARCHAR(255) | ID from source system (optional) |
| `payload` | JSON | Transformed data record |
| `created_at` | TIMESTAMP | When record was created |
| `updated_at` | TIMESTAMP | When record was last updated |

## Transformation Types

| Type | Description | Example Config |
|---|---|---|
| `coerce` | Type conversion (int, float, bool) | `{"type": "float", "default": 0.0}` |
| `default` | Fill nulls with a default value | `{"default": "unknown"}` |
| `map` | Map values through a lookup table | `{"map": {"old_val": "new_val"}}` |
| `drop` | Remove field from record | `{}` |
| `custom` | Registered Python function (advanced) | `{"fn": "my_transform"}` |