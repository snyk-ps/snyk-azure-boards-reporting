## Why

Changes 0–2 proved ADO read paths, canonical document transform, and standalone Elasticsearch ingest (`azure-devops-smoke wiql`, `elasticsearch-smoke index-one`). The `work-item-export-lifecycle` spec defines the scheduled export run (discover → hydrate → normalize → bulk upsert), but no `export` command exists. Operators cannot run an end-to-end pipeline from config to Kibana-ready index without manual glue.

## What Changes

- Add **`export`** CLI subcommand wiring ADO client → `build_reporting_document()` → `ElasticsearchIngestClient.bulk_upsert_documents()`
- Load scope and policy from YAML (`--config`, `REPORTING_APP_CONFIG`, or documented container default)
- CLI scope overrides mirroring smoke: **`--org`**, **`--project`**, **`--filter-tag`** (CLI wins over config)
- Generate **`export_run_id`** (UUID) on every run; stamp on all documents per R1-FR-EXP-8
- Process config scope per R1-FR-EXP-2 when CLI does not narrow scope (all orgs; empty `projects` → list all projects)
- Chunk WIQL IDs at 200 for batch hydration; bulk upsert with stable `_id` per R1-FR-ES-3
- Emit **`export_summary`** NDJSON on stdout per R1-FR-OBS-3 (`work_items_discovered`, `documents_written`, `documents_failed`, `export_outcome`)
- Wire **`integration_http`** audit records for ADO and ES per R1-FR-OBS-2
- Replace README scaffold with operator docs: env vars, `export` usage, minimum Kibana data view + Lens table (R1-FR-KIB-2)
- Extend `CONFIGURATION.md` with `export` flags and precedence; note Kibana setup lives in README

**Deferred (not in this change):**

| Deferred | Why |
|----------|-----|
| Mapping store enrich (R1-FR-EXP-6) | Optional `snyk` object; ingest accepts docs without it |
| Kibana saved-object NDJSON in repo | v2; manual README steps satisfy R1-FR-KIB-7 for v1 |
| Full dashboards (status/severity charts, R1-FR-KIB-3–6) | Minimum Lens table first; charts documented as follow-up |
| Alert rule IaC (R1-FR-OBS-4 infra) | Documentation-only alerting guidance |

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `work-item-export-lifecycle`: Add CLI scope flags (R1-FR-EXP-10), config resolution (R1-FR-EXP-11), orchestration module requirement (R1-FR-EXP-12)
- `observability`: Export command SHALL wire R1-FR-OBS-2 and R1-FR-OBS-3 (implementation delta R1-FR-OBS-6)
- `application-config`: Export SHALL resolve config path without explicit `--config` when `REPORTING_APP_CONFIG` or default path is set (R1-FR-CFG-11)
- `kibana-reporting`: README SHALL document minimum manual data view + Lens table setup (R1-FR-KIB-9)

## Impact

- **Code**: `src/commands/export.py` (CLI), `src/export/runner.py` (orchestration); wire in `src/main.py`; optional thin logging helper under `src/observability/`
- **Tests**: `tests/commands/test_export.py`, `tests/export/test_runner.py` with injectable ADO + ES transports
- **Docs**: Replace README scaffold; extend CONFIGURATION.md; minor CONTRIBUTING.md layout note for new modules
- **Systems**: Read-only ADO; ES bulk upsert to configured index; stdout NDJSON audit stream
