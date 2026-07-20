# Upstream integration contract

## Purpose

Define the **read-side contract** between [snyk-azure-boards-integration](https://github.com/snyk-ps/snyk-azure-boards-integration) (upstream sync) and **snyk-azure-boards-reporting** (this repository). Reporting SHALL parse Azure DevOps work items assuming upstream behavior documented here. When upstream changes tag vocabulary or mapping schema, **`contract_version`** in this spec SHALL increment.

**`contract_version`:** `1`

## Upstream reference

| Topic | Upstream location |
|-------|-------------------|
| Tag writing (P2-FR-10) | `openspec/specs/sync-lifecycle/spec.md` |
| Managed severity/type tags | `openspec/changes/archive/2026-05-12-snyk-severity-type-work-item-tags/` |
| Operator tag configuration | `CONFIGURATION.md` § Work item tags |
| Mapping store schema | `src/mapping_store/schema.py` |

## Requirements

### Requirement: Contract version (R1-FR-UP-1)

This capability SHALL declare **`contract_version: 1`**. When [snyk-azure-boards-integration](https://github.com/snyk-ps/snyk-azure-boards-integration) changes managed tag prefixes, severity levels, type suffix mapping, or mapping store columns material to reporting, this spec SHALL increment **`contract_version`** and document migration notes for operators and parsers.

#### Scenario: Parser checks contract version

- **WHEN** application configuration sets `upstream_contract_version: 1`
- **THEN** the tag parser SHALL use the vocabulary defined in this spec at version 1

---

### Requirement: System.Tags format (R1-FR-UP-2)

Upstream sync writes **`System.Tags`** as a **semicolon-separated** string (Azure DevOps convention). Tags appear in this order:

1. **Operator tags** from merged `work_item_template.tags` (after reserved-prefix stripping).
2. **Managed severity tag** (if derivable): `Snyk-Severity-{level}`.
3. **Managed type tag** (if derivable): `Snyk-Type-{suffix}`.

Operator-supplied tags whose names start with **`Snyk-Severity-`** or **`Snyk-Type-`** are **stripped** by upstream; managed tags from Snyk issue data are authoritative for those dimensions.

#### Scenario: Standard tagged work item

- **WHEN** upstream sync has run for an origin-included issue with operator tag `Snyk`, severity `high`, and Snyk type `package_vulnerability`
- **THEN** `System.Tags` SHALL contain `Snyk`, `Snyk-Severity-high`, and `Snyk-Type-open_source` in that order

#### Scenario: Operator tags without managed type

- **WHEN** severity normalizes to `critical` but Snyk issue type cannot be mapped
- **THEN** `System.Tags` MAY contain `Snyk-Severity-critical` and SHALL omit any `Snyk-Type-*` tag for that work item

---

### Requirement: Managed severity tag vocabulary (R1-FR-UP-3)

Upstream emits **at most one** severity managed tag of the form **`Snyk-Severity-{level}`** where **`level`** is one of:

| Level |
|-------|
| `low` |
| `medium` |
| `high` |
| `critical` |

Levels are normalized to lowercase from Snyk **`effective_severity_level`**. Missing or unrecognized levels produce **no** severity managed tag.

Reporting parsers SHALL extract **`level`** as the substring after the `Snyk-Severity-` prefix.

#### Scenario: Parse severity from tags

- **WHEN** `System.Tags` contains `Snyk; Snyk-Severity-high; Snyk-Type-code`
- **THEN** parsed severity SHALL be `high`

---

### Requirement: Managed finding-type tag vocabulary (R1-FR-UP-4)

Upstream emits **at most one** type managed tag of the form **`Snyk-Type-{suffix}`**. The **`suffix`** is derived from Snyk issue **`attributes.type`** (or equivalent normalized token) using this mapping (after normalization: strip, lowercase, hyphens and spaces → underscores):

| Snyk type token | Tag suffix | Example tag |
|-----------------|------------|-------------|
| `package_vulnerability` | `open_source` | `Snyk-Type-open_source` |
| `package`, `open_source`, `opensource`, `dependency`, `vulnerability` | `open_source` | `Snyk-Type-open_source` |
| `code`, `sast` | `code` | `Snyk-Type-code` |
| `container`, `image` | `container` | `Snyk-Type-container` |
| `cloud`, `config`, `iac`, `configuration`, `terraform`, `cloudformation`, `cloud_formation`, `kubernetes` | `iac` | `Snyk-Type-iac` |
| `license`, `licensing` | `license` | `Snyk-Type-license` |
| `custom` | `custom` | `Snyk-Type-custom` |

Unmapped tokens produce **no** type managed tag.

Reporting parsers SHALL extract **`suffix`** as the substring after the `Snyk-Type-` prefix.

#### Scenario: Parse finding type from tags

- **WHEN** `System.Tags` contains `Snyk-Type-iac`
- **THEN** parsed finding type SHALL be `iac`

---

### Requirement: Operator filter tag (R1-FR-UP-5)

Upstream operators configure at least one **operator tag** (commonly **`Snyk`**) in `work_item_template.tags` to mark work items created by the integration. Reporting WIQL filters SHALL default to **`Snyk`** but MUST remain configurable because operators may use different labels (for example per-`org_mappings` overrides).

Work items **never touched by upstream sync** may lack managed tags; filtering on operator tag alone MAY include incomplete records.

#### Scenario: Default WIQL filter tag

- **WHEN** application configuration omits `filter_tag`
- **THEN** WIQL SHALL use `[System.Tags] CONTAINS 'Snyk'` as the default filter

---

### Requirement: Work item state contract (R1-FR-UP-6)

Upstream sync sets **`System.State`** using operator-configured values:

- **`work_item_state_active`** — active/open findings (example: `To Do`, `New`).
- **`work_item_state_closed`** — close path for Snyk resolved/ignored findings (example: `Done`, `Closed`).

Reporting SHALL treat closed states as **configurable** in application configuration (`reporting.closed_states`) because they vary by operator process template. Upstream defaults in sync repo are `New` / `Closed`; production configs may differ.

#### Scenario: Closed state from operator YAML

- **WHEN** upstream uses `work_item_state_closed: Done` and a finding is resolved
- **THEN** exported `work_item.status` SHALL be `Done` and reporting closed-state logic SHALL include `Done` when configured

---

### Requirement: Fields not written by upstream (R1-FR-UP-7)

Upstream sync does **not** populate ADO lifecycle date fields directly. Reporting SHALL read these from Azure DevOps API responses:

| Field | ADO reference field |
|-------|---------------------|
| Creation date | `System.CreatedDate` |
| Last change | `System.ChangedDate` |
| Closure | `Microsoft.VSTS.Common.ClosedDate` (preferred) |
| Resolution | `Microsoft.VSTS.Common.ResolvedDate` (fallback) |

#### Scenario: Creation date from ADO

- **WHEN** a work item is exported and ADO returns `System.CreatedDate`
- **THEN** the reporting document SHALL use that value for `work_item.created_at` regardless of mapping store timestamps

---

### Requirement: Optional mapping store enrich (R1-FR-UP-8)

When configured, reporting MAY read the upstream **issues sync persistence** store (Azure Table Storage or SQLite) to enrich export documents. Minimum columns (snake_case), matching upstream schema:

| Column | Role |
|--------|------|
| `group_id`, `org_id`, `project_id`, `issue_id` | Snyk issue identity |
| `snyk_status` | Derived lifecycle: `open`, `resolved`, `ignored` |
| `organization`, `project` | ADO routing |
| `work_item_id`, `work_item_status` | Boards link (may lag one sync behind ADO) |
| `snyk_project_name`, `snyk_project_origin` | Snyk project metadata |
| `excluded`, `exclusion_reason` | Origin policy exclusion |
| `created_at`, `updated_at` | Mapping row metadata (UTC ISO 8601) — **not** work item dates |

Join key: **`work_item_id`** matched to exported ADO **`System.Id`**.

#### Scenario: Enrich with Snyk issue id

- **WHEN** mapping store is enabled and a row exists for `work_item_id` 12345
- **THEN** the export document SHALL include `snyk.issue_id` and `snyk.status` from that row

---

### Requirement: Legacy and incomplete work items (R1-FR-UP-9)

Work items created before managed tags were introduced, or never updated by sync, MAY lack `Snyk-Severity-*` or `Snyk-Type-*` tags. Reporting parsers SHALL set parsed severity and finding type to **`null`** rather than inferring from description text.

#### Scenario: Missing managed tags

- **WHEN** `System.Tags` is `Snyk` only
- **THEN** parsed `tags.severity` and `tags.finding_type` SHALL be `null` and the document SHALL still be exported
