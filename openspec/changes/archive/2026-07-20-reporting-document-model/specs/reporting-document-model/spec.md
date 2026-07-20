## ADDED Requirements

### Requirement: Pure transform API (R1-FR-DOC-7)

The application SHALL expose a pure Python transform that maps a client-normalized work item and export context to a reporting document per R1-FR-DOC-1 through R1-FR-DOC-5.

The transform SHALL NOT perform network I/O or read secrets.

Input SHALL be the normalized work item shape produced by `azure-devops-reporting-client` (`work_item_id`, `work_item_status`, `fields`).

#### Scenario: Build document without mapping enrich

- **WHEN** `build_reporting_document` is called with a normalized item and context without a mapping row
- **THEN** the result SHALL contain `work_item`, `tags`, and `export` and SHALL omit `snyk`

#### Scenario: Stable output for fixed context

- **WHEN** the same normalized item and transform context are supplied twice
- **THEN** the resulting JSON objects SHALL be deeply equal

#### Scenario: Closure and tags from ADO fields

- **WHEN** a normalized item has `System.Tags` `Snyk; Snyk-Severity-high; Snyk-Type-code`, `System.State` `Done`, and `Microsoft.VSTS.Common.ClosedDate`
- **THEN** the document SHALL populate `tags.severity`, `tags.finding_type`, `work_item.closed_at`, and `work_item.days_to_close` per R1-FR-DOC-2, R1-FR-DOC-3, and `work-item-export-lifecycle` R1-FR-EXP-5
