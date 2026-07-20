# Kibana reporting (v2)

## Purpose

Define **dashboard and visualization requirements** for operators using Kibana against the Elasticsearch index populated by export. Implementation is Kibana configuration (Lens, saved searches, dashboards) — not Python application code.

**Status:** v2 — implement after v1 export pipeline and index are operational.

## Prerequisites

- Index **`snyk-ado-work-items`** (or configured name) populated per `reporting-document-model`.
- Field mappings applied per `elasticsearch-platform`.

## Requirements

### Requirement: Global filters (R1-FR-KIB-1)

Dashboards SHALL provide filters for:

| Filter | Field |
|--------|-------|
| Organization | `work_item.organization` |
| Project | `work_item.project` |
| Severity | `tags.severity` |
| Finding type | `tags.finding_type` |
| Status | `work_item.status` |
| Operator tag | `tags.operator` |

#### Scenario: Filter by severity

- **WHEN** an operator selects severity `critical`
- **THEN** all panels on the dashboard SHALL respect the global filter

---

### Requirement: Work item detail table (R1-FR-KIB-2)

A primary table visualization SHALL display:

| Column | Field |
|--------|-------|
| Work item ID | `work_item.id` |
| Title | `work_item.title` |
| Project | `work_item.project` |
| Status | `work_item.status` |
| Severity | `tags.severity` |
| Finding type | `tags.finding_type` |
| Created | `work_item.created_at` |
| Closed | `work_item.closed_at` |
| Days to close | `work_item.days_to_close` |

Rows SHALL be sortable by creation date and closure date.

#### Scenario: Sort by creation date

- **WHEN** the operator sorts the table by created descending
- **THEN** newest work items appear first

---

### Requirement: Status breakdown (R1-FR-KIB-3)

A chart SHALL show work item counts by **`work_item.status`** (pie or bar).

#### Scenario: Open vs closed counts

- **WHEN** index contains items in `To Do` and `Done`
- **THEN** the chart SHALL show separate counts for each status value present

---

### Requirement: Severity and type breakdowns (R1-FR-KIB-4)

Charts SHALL show distributions for:

- **`tags.severity`** (when not null)
- **`tags.finding_type`** (when not null)

#### Scenario: Severity chart excludes null

- **WHEN** some documents have `tags.severity: null`
- **THEN** the severity chart SHOULD treat null as "unknown" or exclude per operator preference documented in README

---

### Requirement: Time-to-close metric (R1-FR-KIB-5)

A metric or trend panel SHALL show **average `work_item.days_to_close`**, with optional split by **`tags.severity`**.

Only documents where **`work_item.closed_at`** is not null SHALL be included.

#### Scenario: Average days to close by severity

- **WHEN** closed high-severity items average 5 days and critical average 2 days
- **THEN** the panel SHALL show both averages when split by severity

---

### Requirement: Creation trend (R1-FR-KIB-6)

A time-series panel SHALL histogram **`work_item.created_at`** (daily or weekly bucket) with optional split by **`tags.severity`**.

#### Scenario: Monthly creation trend

- **WHEN** operator selects last 90 days
- **THEN** the histogram SHALL show creation volume over time

---

### Requirement: Saved objects delivery (R1-FR-KIB-7)

Saved searches, visualizations, and dashboards MAY be:

- Documented as manual setup steps in README, **or**
- Exported as Kibana saved-object NDJSON checked into the repository under a documented path (for example `kibana/saved_objects/`).

Automated import on deploy is **out of scope** for v1.

#### Scenario: Saved objects in repo

- **WHEN** the repository includes `kibana/saved_objects/dashboard.ndjson`
- **THEN** README SHALL document import steps via Kibana Stack Management

---

### Requirement: Non-goals (R1-FR-KIB-8)

Kibana capability does NOT require:

- Unit tests in Python for dashboard JSON.
- Embedded Kibana iframes in other applications.
- Real-time refresh faster than export schedule (near-real-time is bounded by export cadence).
