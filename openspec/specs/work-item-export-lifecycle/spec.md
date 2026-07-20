# Work item export lifecycle

## Purpose

Define the **scheduled export run** that discovers Snyk-related Azure DevOps work items, normalizes them into reporting documents, and hands them to Elasticsearch ingest. This capability orchestrates `azure-devops-reporting-client`, `reporting-document-model`, optional mapping store enrich, and `elasticsearch-platform`.

## Requirements

### Requirement: Export CLI entry point (R1-FR-EXP-1)

The application SHALL provide an **`export`** subcommand (argparse) that:

1. Loads application configuration (YAML path via `--config` and/or environment).
2. Runs one logical **export run** to completion.
3. Exits non-zero when the run fails catastrophically (configuration error, auth failure, Elasticsearch unreachable).

Secrets (`AZURE_DEVOPS_PAT`, Elasticsearch credentials) SHALL come from environment variables only.

#### Scenario: Successful export run

- **WHEN** `export --config /config/reporting.yaml` runs with valid credentials and matching work items
- **THEN** the process SHALL complete with exit code 0 and emit an export summary audit record

---

### Requirement: Organization and project scope (R1-FR-EXP-2)

Each export run SHALL process every **`azure_devops.organizations[]`** entry in configuration. For each organization:

- If **`projects`** is empty, enumerate all ADO projects and WIQL-query each.
- If **`projects`** is non-empty, WIQL-query only listed project names.

#### Scenario: All projects in org

- **WHEN** configuration lists org `torstencannell` with `projects: []`
- **THEN** export SHALL WIQL-query every project returned by the list-projects API

#### Scenario: Restricted project allowlist

- **WHEN** configuration lists `projects: [snykDemoProject]`
- **THEN** export SHALL WIQL-query only `snykDemoProject`

---

### Requirement: Discover → query → hydrate pipeline (R1-FR-EXP-3)

For each organization/project pair, export SHALL:

1. Execute WIQL with configured **`filter_tag`** (default `Snyk`).
2. Chunk returned work item IDs into batches of at most **200**.
3. Hydrate each batch via work items batch.
4. Normalize each hydrated item per `reporting-document-model`.

#### Scenario: Large result set chunked

- **WHEN** WIQL returns 450 work item IDs
- **THEN** export SHALL perform three batch calls (200 + 200 + 50)

---

### Requirement: Reporting dimensions (R1-FR-EXP-4)

Each exported document SHALL populate:

| Dimension | Source |
|-----------|--------|
| Creation date | `System.CreatedDate` |
| Closure / resolution date | See R1-FR-EXP-5 |
| Current status | `System.State` |
| Tags (severity, finding type) | Parse `System.Tags` per `upstream-integration-contract` |

#### Scenario: All four dimensions present

- **WHEN** ADO returns created date, closed date, state `Done`, and tags `Snyk; Snyk-Severity-high; Snyk-Type-code`
- **THEN** the document SHALL include `work_item.created_at`, `work_item.closed_at`, `work_item.status`, `tags.severity`, and `tags.finding_type`

---

### Requirement: Closure date resolution (R1-FR-EXP-5)

Export SHALL derive **`work_item.closed_at`** using this precedence:

1. `Microsoft.VSTS.Common.ClosedDate` when present.
2. Else `Microsoft.VSTS.Common.ResolvedDate` when present.
3. Else when `System.State` is in configured **`reporting.closed_states`**, use `System.ChangedDate` as a fallback closure proxy.
4. Else `null`.

When both `closed_at` and `created_at` are present, export SHALL compute **`days_to_close`** as the difference in days (UTC).

#### Scenario: ClosedDate preferred

- **WHEN** `ClosedDate` and `ResolvedDate` are both present
- **THEN** `work_item.closed_at` SHALL use `ClosedDate`

#### Scenario: Fallback when state is closed

- **WHEN** `ClosedDate` and `ResolvedDate` are absent, `System.State` is `Done`, and `Done` is in `closed_states`
- **THEN** `work_item.closed_at` SHALL fall back to `System.ChangedDate`

#### Scenario: Active work item

- **WHEN** `System.State` is `To Do` and no closure dates are present
- **THEN** `work_item.closed_at` SHALL be `null` and `days_to_close` SHALL be `null`

---

### Requirement: Optional mapping store join (R1-FR-EXP-6)

When **`mapping_store`** is configured, export MAY load rows keyed by **`work_item_id`** and merge Snyk fields into the document per `upstream-integration-contract` R1-FR-UP-8.

Mapping store absence or a missing row SHALL NOT fail export for an otherwise valid work item.

#### Scenario: No mapping row

- **WHEN** mapping store is enabled but no row exists for work item 999
- **THEN** export SHALL still emit the document with `snyk` fields absent or null

---

### Requirement: Idempotent export runs (R1-FR-EXP-7)

Repeated export runs SHALL upsert documents to Elasticsearch using a stable document id per `elasticsearch-platform`. Re-exporting the same work item SHALL update the existing document, not create duplicates.

#### Scenario: Second run updates document

- **WHEN** work item 12345 was exported yesterday and is exported again today with an updated `System.State`
- **THEN** Elasticsearch SHALL contain one document for that work item with the latest status

---

### Requirement: Export run identity (R1-FR-EXP-8)

Each export run SHALL generate a **`export_run_id`** (UUID or equivalent unique string) included on every document and in observability summary logs.

#### Scenario: Run id on documents

- **WHEN** an export run starts
- **THEN** all documents written in that run SHALL share the same `export.run_id`

---

### Requirement: Non-goals (R1-FR-EXP-9)

Export SHALL NOT:

- Create, update, or close Azure DevOps work items.
- Call the Snyk Issues API (Snyk data comes from optional mapping store or parsed tags only).
- Replace upstream sync or modify the mapping store.

#### Scenario: Read-only ADO

- **WHEN** export completes successfully
- **THEN** no Azure DevOps mutation HTTP methods SHALL have been invoked
