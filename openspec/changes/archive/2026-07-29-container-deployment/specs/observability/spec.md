## ADDED Requirements

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
