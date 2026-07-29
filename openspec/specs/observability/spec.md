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

### Requirement: Export command wires audit logging (R1-FR-OBS-6)

The **`export`** command implementation SHALL emit `integration_http` audit records per R1-FR-OBS-2 for terminal ADO and Elasticsearch HTTP requests, and exactly one `export_summary` record per R1-FR-OBS-3 at run completion.

#### Scenario: Summary includes discovered and failed counts

- **WHEN** export discovers 10 work items and 1 bulk line fails
- **THEN** `export_summary` SHALL report `work_items_discovered=10`, `documents_written=9`, `documents_failed=1`, and `export_outcome=partial`

### Requirement: Container log shipping (R1-FR-OBS-7)

For container deployments, **`export`** NDJSON on stdout SHALL be suitable for Azure Log Analytics ingestion (for example `ContainerAppConsoleLogs_CL`).

Operator documentation SHALL describe:

- **`PYTHONUNBUFFERED=1`** set in the Dockerfile for timely log delivery
- Example Kusto query filtering `export_summary` and `integration_http` events from parsed NDJSON console lines
- Using summary duration and outcome fields to size **replica timeout** on Container App Jobs

#### Scenario: Log Analytics export failure query

- **WHEN** console logs land in Log Analytics as NDJSON lines
- **THEN** operators SHALL be able to filter failed exports using parsed `export_outcome` not equal to `success`

#### Scenario: Timeout tuning from summary

- **WHEN** an operator reviews `export_summary` records from a test job run
- **THEN** README SHALL explain setting replica timeout above observed run duration with margin

