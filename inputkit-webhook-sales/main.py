
import json
import hashlib
from typing import Dict
from flask import Request
from google.cloud import bigquery
from google.api_core.exceptions import NotFound, Conflict

# -----------------------------
# 🔒 Static values (hardcoded)
# -----------------------------
# Replace these with your actual values and keep them consistent everywhere.

BQ_PROJECT_ID = "advanced-analytics-397015"          # <-- your GCP project ID
BQ_DATASET_ID = "Raw_Inputkit_Survey"                   # <-- your BigQuery dataset name
BQ_TABLE_ID   = "survey_events"              # <-- your BigQuery table name
WEBHOOK_TOKEN = "Xx93jksdf8DFjklsf9033"  # <-- your shared secret for the webhook

# Fully-qualified table name
TABLE_FQN = f"{BQ_PROJECT_ID}.{BQ_DATASET_ID}.{BQ_TABLE_ID}"

# BigQuery client bound to the hardcoded project
bq = bigquery.Client(project=BQ_PROJECT_ID)

def _event_id(payload: Dict) -> str:
    """Deterministic id for idempotency (best-effort de-dupe in BigQuery)."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def _ensure_table_exists():
    """Create destination table lazily on first POST."""
    try:
        bq.get_table(TABLE_FQN)
        return
    except NotFound:
        pass

    schema = [
        bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField(
            "raw_payload", "JSON",
            description="Full webhook body; structure preserved exactly"
        ),
        bigquery.SchemaField(
            "received_at", "TIMESTAMP",
            default_value_expression="CURRENT_TIMESTAMP()"
        ),
    ]

    table = bigquery.Table(TABLE_FQN, schema=schema)

    # Partition by ingestion time (received_at) and cluster by event_id
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="received_at",
    )
    table.clustering_fields = ["event_id"]

    try:
        bq.create_table(table)
    except Conflict:
        # If another instance created it concurrently, continue safely
        pass

def inputkit_webhook(request: Request):
    if request.method != "POST":
        return ("Only POST allowed", 405)

    # Simple shared-secret guard
    token = request.args.get("token") or request.headers.get("X-Webhook-Token")
    if WEBHOOK_TOKEN and token != WEBHOOK_TOKEN:
        return ("Unauthorized", 401)

    if not request.is_json:
        return ("Content-Type must be application/json", 415)

    payload = request.get_json(silent=True)
    if payload is None:
        return ("Invalid JSON", 400)

    # 1) Lazy table creation
    _ensure_table_exists()

    # 2) Build the row
    eid = _event_id(payload)
    row = {
        "event_id": eid,
        "raw_payload": json.dumps(payload, separators=(",", ":")),
        # received_at defaults server-side
    }

    # 3) Stream insert with insertId for de-dupe (best effort)
    errors = bq.insert_rows_json(
        TABLE_FQN,
        json_rows=[row],
        row_ids=[eid],               # sets insertId under the hood
        skip_invalid_rows=False,
        ignore_unknown_values=False, # we only insert defined columns
    )

    if errors:
        return (json.dumps({"status": "bq_insert_failed", "errors": errors}), 500)

    return (json.dumps({"status": "ok", "event_id": eid}), 200)


