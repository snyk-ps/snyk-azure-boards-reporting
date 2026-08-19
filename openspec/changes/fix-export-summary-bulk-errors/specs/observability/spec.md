## MODIFIED Requirements

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

When present, each entry in **`errors`** SHALL be a **JSON string** (not a nested object or opaque Python type) so that the full audit record serializes with stdlib `json.dumps`.

#### Scenario: Successful run summary

- **WHEN** export completes with all documents written
- **THEN** `export_outcome` SHALL be `success` and `documents_failed` SHALL be 0

#### Scenario: Partial bulk failure

- **WHEN** some bulk lines fail but the run completes
- **THEN** `export_outcome` SHALL be `partial` and counts SHALL reflect successes and failures

#### Scenario: Bulk failure errors are JSON-serializable

- **WHEN** export completes with one or more Elasticsearch bulk item failures
- **THEN** the application SHALL emit one valid `export_summary` NDJSON line on stdout
- **AND** each element of `record.errors` SHALL be a string containing the failed document id and Elasticsearch error type/reason

### Requirement: Export command wires audit logging (R1-FR-OBS-6)

The **`export`** command implementation SHALL emit `integration_http` audit records per R1-FR-OBS-2 for terminal ADO and Elasticsearch HTTP requests, and exactly one `export_summary` record per R1-FR-OBS-3 at run completion.

The **`export_summary`** record SHALL NOT be omitted due to non-serializable content in the `errors` field.

#### Scenario: Summary includes discovered and failed counts

- **WHEN** export discovers 10 work items and 1 bulk line fails
- **THEN** `export_summary` SHALL report `work_items_discovered=10`, `documents_written=9`, `documents_failed=1`, and `export_outcome=partial`

#### Scenario: Summary emitted after total bulk failure

- **WHEN** export discovers work items and every bulk line fails
- **THEN** `export_summary` SHALL still be emitted with `documents_written=0`, `documents_failed` greater than 0, and `export_outcome=failure`
