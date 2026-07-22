## ADDED Requirements

### Requirement: Export command wires audit logging (R1-FR-OBS-6)

The **`export`** command implementation SHALL emit `integration_http` audit records per R1-FR-OBS-2 for terminal ADO and Elasticsearch HTTP requests, and exactly one `export_summary` record per R1-FR-OBS-3 at run completion.

#### Scenario: Summary includes discovered and failed counts

- **WHEN** export discovers 10 work items and 1 bulk line fails
- **THEN** `export_summary` SHALL report `work_items_discovered=10`, `documents_written=9`, `documents_failed=1`, and `export_outcome=partial`
