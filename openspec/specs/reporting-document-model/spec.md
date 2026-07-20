# Reporting document model

## Purpose

Define the **normalized JSON document** written to Elasticsearch for each exported Azure DevOps work item. Kibana dashboards consume this schema.

Tag parsing rules SHALL align with `upstream-integration-contract` **`contract_version: 1`**.

## Requirements

### Requirement: Document top-level structure (R1-FR-DOC-1)

Each export document SHALL be a JSON object with these top-level keys:

| Key | Type | Required |
|-----|------|----------|
| `work_item` | object | yes |
| `tags` | object | yes |
| `export` | object | yes |
| `snyk` | object | no (when mapping store enrich enabled) |

#### Scenario: Minimum document

- **WHEN** a work item is exported without mapping store enrich
- **THEN** the document SHALL contain `work_item`, `tags`, and `export` and MAY omit `snyk`

---

### Requirement: work_item object (R1-FR-DOC-2)

| Field | ES mapping type | Source |
|-------|-----------------|--------|
| `work_item.id` | `keyword` | `System.Id` |
| `work_item.organization` | `keyword` | Export config org name |
| `work_item.project` | `keyword` | `System.TeamProject` |
| `work_item.title` | `text` (+ `keyword` subfield) | `System.Title` |
| `work_item.status` | `keyword` | `System.State` |
| `work_item.area_path` | `keyword` | `System.AreaPath` |
| `work_item.created_at` | `date` | `System.CreatedDate` (UTC ISO 8601) |
| `work_item.changed_at` | `date` | `System.ChangedDate` |
| `work_item.closed_at` | `date` | Per `work-item-export-lifecycle` R1-FR-EXP-5; nullable |
| `work_item.days_to_close` | `float` | Computed; nullable |

#### Scenario: Active item has null closure fields

- **WHEN** work item is active with no closure dates
- **THEN** `work_item.closed_at` and `work_item.days_to_close` SHALL be JSON `null`

---

### Requirement: tags object (R1-FR-DOC-3)

| Field | ES mapping type | Derivation |
|-------|-----------------|------------|
| `tags.raw` | `keyword` | Full `System.Tags` string |
| `tags.operator` | `keyword` (multi) | Tags not matching `Snyk-Severity-*` or `Snyk-Type-*` |
| `tags.severity` | `keyword` | Parsed from `Snyk-Severity-{level}`; `null` if absent |
| `tags.finding_type` | `keyword` | Parsed from `Snyk-Type-{suffix}`; `null` if absent |

Parsing SHALL split `System.Tags` on `;`, trim whitespace, and apply prefix rules from `upstream-integration-contract`.

#### Scenario: Parse operator and managed tags

- **WHEN** `System.Tags` is `Snyk; Snyk-Severity-critical; Snyk-Type-open_source`
- **THEN** `tags.operator` SHALL be `["Snyk"]`, `tags.severity` SHALL be `critical`, and `tags.finding_type` SHALL be `open_source`

#### Scenario: Empty tags

- **WHEN** `System.Tags` is absent or empty
- **THEN** `tags.raw` SHALL be empty string, `tags.operator` SHALL be `[]`, and severity/type SHALL be `null`

---

### Requirement: snyk object (optional enrich) (R1-FR-DOC-4)

When mapping store join succeeds:

| Field | ES mapping type | Source column |
|-------|-----------------|---------------|
| `snyk.group_id` | `keyword` | `group_id` |
| `snyk.org_id` | `keyword` | `org_id` |
| `snyk.project_id` | `keyword` | `project_id` |
| `snyk.issue_id` | `keyword` | `issue_id` |
| `snyk.status` | `keyword` | `snyk_status` |
| `snyk.project_name` | `keyword` | `snyk_project_name` |
| `snyk.project_origin` | `keyword` | `snyk_project_origin` |
| `snyk.excluded` | `boolean` | `excluded` |
| `snyk.exclusion_reason` | `keyword` | `exclusion_reason` |
| `snyk.mapping_updated_at` | `date` | mapping row `updated_at` |

#### Scenario: Enriched document

- **WHEN** mapping row exists for work item 42
- **THEN** `snyk.issue_id` and `snyk.status` SHALL be populated from the row

---

### Requirement: export object (R1-FR-DOC-5)

| Field | ES mapping type | Source |
|-------|-----------------|--------|
| `export.run_id` | `keyword` | Export run UUID |
| `export.exported_at` | `date` | UTC timestamp when document was built |

#### Scenario: Export metadata on every document

- **WHEN** a document is written during run `abc-123`
- **THEN** `export.run_id` SHALL be `abc-123`

---

### Requirement: Example document (R1-FR-DOC-6)

Normative example (illustrative values):

```json
{
  "work_item": {
    "id": "12345",
    "organization": "torstencannell",
    "project": "snykDemoProject",
    "title": "[HIGH] example-package: CVE-2024-0001",
    "status": "Done",
    "area_path": "snykDemoProject",
    "created_at": "2026-01-15T10:00:00.000Z",
    "changed_at": "2026-02-01T14:30:00.000Z",
    "closed_at": "2026-02-01T14:30:00.000Z",
    "days_to_close": 17.19
  },
  "tags": {
    "raw": "Snyk; Snyk-Severity-high; Snyk-Type-open_source",
    "operator": ["Snyk"],
    "severity": "high",
    "finding_type": "open_source"
  },
  "snyk": {
    "issue_id": "uuid-here",
    "status": "resolved",
    "project_origin": "github-enterprise"
  },
  "export": {
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "exported_at": "2026-07-20T21:00:00.000Z"
  }
}
```

#### Scenario: Example validates against schema

- **WHEN** implementers use the example as a fixture
- **THEN** all required keys in R1-FR-DOC-1 through R1-FR-DOC-5 SHALL be present
