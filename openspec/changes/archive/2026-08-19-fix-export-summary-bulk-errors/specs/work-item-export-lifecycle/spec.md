## MODIFIED Requirements

### Requirement: Export orchestration module (R1-FR-EXP-12)

The application SHALL implement export orchestration that composes existing integrations without duplicating ADO or ES HTTP logic:

1. Resolve scope
2. ADO WIQL + batch hydrate (R1-FR-EXP-3)
3. `build_reporting_document()` per item (R1-FR-EXP-4, R1-FR-EXP-5)
4. Elasticsearch bulk upsert (R1-FR-EXP-7)

When bulk upsert returns per-item failures, orchestration SHALL record them as string error summaries suitable for `export_summary` emission (R1-FR-OBS-3).

#### Scenario: End-to-end single project

- **WHEN** export runs for one project with matching work items and valid ES credentials
- **THEN** Elasticsearch SHALL contain upserted reporting documents and stdout SHALL include `export_summary` with matching discovered and written counts

#### Scenario: Bulk failures still produce export summary

- **WHEN** export runs for one project with matching work items and Elasticsearch rejects one or more bulk lines
- **THEN** stdout SHALL include `export_summary` with accurate `documents_written`, `documents_failed`, and string `errors` entries
- **AND** the command SHALL NOT crash during audit logging
