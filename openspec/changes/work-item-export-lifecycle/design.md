## Context

Existing pieces:

| Layer | Module | Role |
|-------|--------|------|
| Config | `src/config/loader.py` | org scope, `closed_states`, `elasticsearch.*` |
| ADO | `AzureDevOpsReportingClient` | `list_projects`, `query_work_item_ids`, `get_work_items_batch` |
| Transform | `build_reporting_document()` | R1-FR-DOC-* + R1-FR-EXP-5 closure |
| ES | `ElasticsearchIngestClient` | `ensure_index`, `bulk_upsert_documents` |

Smoke commands prove each layer in isolation; export composes them.

## Goals / Non-Goals

**Goals:**

- One `export` run: config → ADO discover/hydrate → normalize → ES upsert → summary
- Idempotent re-export (stable `_id` per R1-FR-ES-3)
- Operator-friendly docs through first Kibana table

**Non-Goals:**

- Mapping store join (R1-FR-EXP-6)
- Kibana saved-object automation
- Snyk API calls (R1-FR-EXP-9)

## Decisions

### 1. Pipeline flow

```
load_config(path)
resolve_export_scope(config, cli_args) → [(org, project, filter_tag), ...]
export_run_id = uuid4()
context = TransformContext(run_id, exported_at=utcnow(), organization=..., closed_states=...)

if auto_create_index: es.ensure_index(index, mappings=load_index_mappings())

for (org, project, filter_tag) in scope:
  ids = ado.query_work_item_ids(org, project, filter_tag)
  discovered += len(ids)
  for batch in chunk(ids, 200):
    items = ado.get_work_items_batch(org, project, batch)
    docs = [build_reporting_document(i, context=...) for i in items]
    result = es.bulk_upsert_documents(index, docs)
    written += result.succeeded; failed += result.failed

emit export_summary NDJSON
```

`ensure_index` runs once before the first bulk when `auto_create_index: true`.

Document `_id` is derived by the ES client as `{organization}:{project}:{work_item.id}` (R1-FR-ES-3).

### 2. Config resolution (R1-FR-CFG-1)

Precedence for config **path**:

1. `--config <path>`
2. `REPORTING_APP_CONFIG`
3. Documented default `/config/reporting.yaml` (container)

Fail fast with a clear error if no path resolves. Local dev SHOULD pass `--config data/reporting.sample.yaml` explicitly.

### 3. Scope resolution (CLI + YAML)

Mirror `azure-devops-smoke wiql` precedence (`CONFIGURATION.md`):

1. Built-in defaults (`filter_tag: Snyk`)
2. YAML org entry
3. CLI flags (highest)

| Mode | Behavior |
|------|----------|
| **Full config** (no `--org`/`--project`) | Every `organizations[]` entry; per org, `projects: []` → `list_projects()` then WIQL each |
| **Narrowed** (`--org` and/or `--project`) | Single org/project run for local verification; `--project` required when narrowing to one project |
| **`--filter-tag`** | Overrides org's YAML `filter_tag` for the run |

### 4. Stdout contract

Per `observability` spec, **`export` stdout is NDJSON** (not JSONL work items):

- Per-request `integration_http` audit lines during the run
- Final `event=export_summary` with counts operators care about:

```json
{
  "timestamp": "2026-07-21T03:00:00.000Z",
  "level": "INFO",
  "logger": "integration_audit",
  "record": {
    "event": "export_summary",
    "export_run_id": "…",
    "export_duration_seconds": 12.3,
    "export_outcome": "success",
    "organizations_processed": 1,
    "projects_processed": 1,
    "work_items_discovered": 42,
    "documents_written": 42,
    "documents_failed": 0
  }
}
```

Errors go to **stderr** without credentials. Exit code `0` on `success`; non-zero on `failure` or catastrophic error; `partial` → exit `1`.

### 5. Transform errors

Single work item transform failure (missing required field) SHALL increment `documents_failed` and continue (partial run), not abort the entire export — unless ADO/ES auth or config fails (catastrophic).

### 6. Kibana minimum setup (README, not Python)

After a successful export:

1. **Data view**: Stack Management → Data Views → Create → index pattern `snyk-ado-work-items` (or configured name) → time field **`work_item.created_at`**
2. **Discover saved search** (R1-FR-KIB-2 columns): `work_item.id`, `work_item.title`, `work_item.project`, `work_item.status`, `tags.severity`, `tags.finding_type`, `work_item.created_at`, `work_item.closed_at`, `work_item.days_to_close`; sort by `work_item.created_at` desc; document that time filtering uses `work_item.created_at`, not `export.exported_at`
3. **Optional filters** (R1-FR-KIB-1): organization, project, severity, finding type, status

Document that null severity/type is expected when tags omit managed tags.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Large org (all projects) slow | Document project allowlists in YAML; CLI narrowing for dev |
| NDJSON stdout vs human summary | Operators grep `export_summary`; document example in README |
| Partial bulk failures | `export_outcome=partial`; exit 1 |

## Migration Plan

Greenfield command. No data migration. Operators run `export` after `elasticsearch-smoke index-one` succeeds.

## Open Questions

None — default local config requires explicit `--config` or `REPORTING_APP_CONFIG` to avoid accidental runs against wrong scope.
