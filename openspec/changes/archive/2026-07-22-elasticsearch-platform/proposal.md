## Why

Change 0 proved ADO read paths; Change 1 produces canonical reporting documents (`data/reporting-documents.jsonl`). The `elasticsearch-platform` spec defines bulk ingest, idempotent upserts, and index mappings, but no Python client exists yet. We need a standalone ES write path operators and tests can run **without** full export orchestration.

## What Changes

- Implement Elasticsearch ingest client under `src/integrations/elasticsearch/` per R1-FR-ES-1 through R1-FR-ES-6
- Read cluster URL and credentials from environment only (`ELASTICSEARCH_URL`, `ELASTICSEARCH_API_KEY`; basic auth fallback per spec)
- Bulk upsert via `/_bulk` with stable `_id` = `{organization}:{project}:{work_item.id}` (R1-FR-ES-3)
- Extend config loader for `elasticsearch.index_name` and `elasticsearch.auto_create_index` (R1-FR-CFG-4)
- Ship checked-in index mappings JSON aligned with `reporting-document-model` field types (R1-FR-ES-4)
- Optional index create before first bulk when `auto_create_index: true` (R1-FR-ES-6)
- Unit tests using injectable HTTP fake for `/_bulk` (and `PUT /{index}` when auto-create is tested)
- **`elasticsearch-smoke index-one` CLI subcommand** (mirror `azure-devops-smoke wiql` pattern): indexes one hardcoded reporting document into configured index (default `snyk-ado-work-items`)

**Deferred (not in this change):**

| Deferred | Why |
|----------|-----|
| Full `export` orchestration | Composes ADO + transform + this client later |
| Mapping store enrich | Optional `snyk` object; ingest accepts docs as-is |
| Export-run observability (R1-FR-OBS-2/3) | Wire audit + summary when export command exists |
| Kibana saved objects | v2 capability |
| Ingest pipelines / ILM | Explicit non-goals (R1-FR-ES-7) |

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `elasticsearch-platform`: Add standalone ingest client requirement (R1-FR-ES-8), index-setup artifact requirement (R1-FR-ES-9), and smoke CLI requirement (R1-FR-ES-10)
- `application-config`: Loader SHALL expose `elasticsearch` section (R1-FR-CFG-4 implementation)

## Impact

- **Code**: New `src/integrations/elasticsearch/` (auth, client, bulk, mappings, errors); new `src/commands/elasticsearch_smoke.py`; wire subcommand in `src/main.py`; extend `src/config/loader.py`
- **Data**: `data/elasticsearch/snyk-ado-work-items-mappings.json`
- **Tests**: `tests/integrations/elasticsearch/` with HTTP fakes; `tests/commands/test_elasticsearch_smoke.py`; extend `tests/config/test_loader.py`
- **Docs**: Update `CONFIGURATION.md` with `ELASTICSEARCH_*` env vars and `elasticsearch-smoke index-one` usage
- **Dependencies**: stdlib HTTP (`urllib`) only; mirror ADO client transport pattern
