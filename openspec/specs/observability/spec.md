# Observability

## Purpose

Define structured logging and export-run audit events for **snyk-azure-boards-reporting**, mirroring patterns from upstream [snyk-azure-boards-integration](https://github.com/snyk-ps/snyk-azure-boards-integration) `observability` capability (NDJSON stdout, safe HTTP audit).

Functional requirements use **`R1-FR-OBS-*`** IDs.

## Requirements

### Requirement: NDJSON structured CLI logging (R1-FR-OBS-1)

The **`export`** CLI SHALL emit **NDJSON** on **standard output**: one JSON object per line with:

| Key | Role |
|-----|------|
| `timestamp` | UTC RFC 3339 with `Z` |
| `level` | Log level |
| `logger` | Logger name |
| `message` | Optional human message |
| `record` | Optional structured payload object |
| `exception` | Optional on errors |

#### Scenario: Single-line JSON per log record

- **WHEN** the export run logs an audit event
- **THEN** each line SHALL be valid JSON with no embedded unescaped newlines

---

### Requirement: Integration HTTP audit logs (R1-FR-OBS-2)

The application SHALL emit **one** audit record per **terminal** outbound HTTP request to **Azure DevOps** and **Elasticsearch** on logger **`integration_audit`** with **`event=integration_http`**.

Each record SHALL include:

| Field | Role |
|-------|------|
| `duration_ms` | Elapsed time |
| `http_status` | Status code or transport failure class |
| `integration` | `azure_devops` or `elasticsearch` |
| `method` | HTTP method |
| `safe_target` | Host + path pattern without secrets |
| `export_run_id` | When export run is active |

The application SHALL NOT log PATs, API keys, or `Authorization` headers.

#### Scenario: Successful WIQL call audited

- **WHEN** WIQL completes with HTTP 200
- **THEN** logs SHALL contain one `integration_http` record with `integration=azure_devops`

#### Scenario: Elasticsearch auth failure audited safely

- **WHEN** bulk ingest receives HTTP 401
- **THEN** logs SHALL contain an audit record without credential material

---

### Requirement: Export summary (R1-FR-OBS-3)

Once per **`export`** run, the application SHALL emit **`event=export_summary`** on **`integration_audit`** with:

| Field | Role |
|-------|------|
| `export_run_id` | Run identifier |
| `export_duration_seconds` | Wall time for full run |
| `export_outcome` | `success`, `partial`, or `failure` |
| `organizations_processed` | Count |
| `projects_processed` | Count |
| `work_items_discovered` | WIQL id count |
| `documents_written` | Successful ES writes |
| `documents_failed` | Failed ES writes |
| `errors` | Non-secret error summary (optional, bounded length) |

#### Scenario: Successful run summary

- **WHEN** export completes with all documents written
- **THEN** `export_outcome` SHALL be `success` and `documents_failed` SHALL be 0

#### Scenario: Partial bulk failure

- **WHEN** some bulk lines fail but the run completes
- **THEN** `export_outcome` SHALL be `partial` and counts SHALL reflect successes and failures

---

### Requirement: Alerting guidance (R1-FR-OBS-4)

Operator documentation SHALL describe log-based alerts (for example in Elastic Observability or external log shipping):

| Alert | Condition |
|-------|-----------|
| Export failure | `export_outcome=failure` |
| Partial ingest | `export_outcome=partial` |
| Auth failure | `integration_http` with `http_status` 401/403 |
| Slow export | `export_duration_seconds` above operator threshold |

Infrastructure-as-code for alert rules is **out of scope** for v1.

#### Scenario: Auth alert query

- **WHEN** operators configure a log alert on `integration_http` auth failures
- **THEN** documentation SHALL provide an example filter on `http_status` in `[401, 403]`

---

### Requirement: Non-goals (R1-FR-OBS-5)

This capability does NOT require:

- OpenTelemetry custom metrics (v1).
- Application Insights / Log Analytics integration (operators may ship stdout to those platforms).
- Snyk API HTTP audit (export does not call Snyk).
