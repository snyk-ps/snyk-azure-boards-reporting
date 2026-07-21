## Context

Pipeline position:

```
build_reporting_document() → (this change) bulk_upsert_documents() → Elasticsearch
```

Canonical rules: `openspec/specs/elasticsearch-platform/spec.md` R1-FR-ES-1–7, field types from `reporting-document-model`.

Example document (from `data/reporting-documents.jsonl` line 1):

```json
{
  "work_item": {
    "id": "1",
    "organization": "torstencannell",
    "project": "snykDemoProject",
    "title": "NoSQL Injection",
    "status": "To Do"
  },
  "tags": { "raw": "Snyk", "operator": ["Snyk"], "severity": null, "finding_type": null },
  "export": { "run_id": "dev-run", "exported_at": "2026-07-20T23:50:27.020Z" }
}
```

Stable `_id`: `torstencannell:snykDemoProject:1`

Future full export flow (not in this change):

```
WIQL → batch → normalize → build_reporting_document() → bulk_upsert_documents() → Elasticsearch
```

## Goals / Non-Goals

**Goals:**

- Injectable HTTP transport (test with fake; prod with `urllib`)
- Idempotent upsert semantics per R1-FR-ES-3
- Fail fast when `ELASTICSEARCH_URL` unset (R1-FR-ES-1)
- Report per-item bulk success/failure counts (R1-FR-ES-5)
- `elasticsearch-smoke index-one` CLI indexes one hardcoded doc into configured index (exit criteria)
- Mirror `azure-devops-smoke wiql` CLI patterns (argparse subcommands, safe stderr errors)

**Non-Goals:**

- WIQL, PAT, transform, mapping store, full `export` orchestration, Kibana
- Full R1-FR-OBS integration audit (defer to export orchestration change)
- Ingest pipelines / ILM (R1-FR-ES-7)
- Retries beyond minimal handling for 429/5xx on cluster calls

## Decisions

### Module layout

```
src/integrations/elasticsearch/
  auth.py       # resolve credentials from env; build Authorization header
  errors.py     # ElasticsearchHttpError, BulkItemError, ConfigurationError
  mappings.py   # load normative mappings dict / create-index body
  bulk.py       # build NDJSON bulk payload, parse bulk response
  client.py     # ElasticsearchIngestClient — ensure_index, bulk_upsert
  models.py     # BulkResult dataclass
  http.py       # HttpTransport protocol + UrllibTransport (mirror ADO client)

src/commands/
  elasticsearch_smoke.py   # elasticsearch-smoke index-one subcommand
```

### Config wiring

Extend `ReportingAppConfig`:

```python
@dataclass(frozen=True)
class ElasticsearchConfig:
    index_name: str = "snyk-ado-work-items"
    auto_create_index: bool = True

@dataclass(frozen=True)
class ReportingAppConfig:
    organizations: ...
    closed_states: ...
    elasticsearch: ElasticsearchConfig
```

Defaults match R1-FR-CFG-4 when YAML omits `elasticsearch` section.

### Authentication (R1-FR-ES-1)

| Env var | Behavior |
|---------|----------|
| `ELASTICSEARCH_URL` | Required; strip trailing `/` |
| `ELASTICSEARCH_API_KEY` | Preferred; header `Authorization: ApiKey <value>` |
| `ELASTICSEARCH_USERNAME` + `ELASTICSEARCH_PASSWORD` | Basic auth when API key unset |

Never log credentials or full Authorization header.

### Document `_id` (R1-FR-ES-3)

```python
def document_id(doc: dict[str, Any]) -> str:
    wi = doc["work_item"]
    return f"{wi['organization']}:{wi['project']}:{wi['id']}"
```

Validate required keys before bulk; raise clear error if missing.

### Bulk format (R1-FR-ES-5)

Use **`update`** action with **`doc_as_upsert: true`**:

```ndjson
{"update":{"_index":"snyk-ado-work-items","_id":"torstencannell:snykDemoProject:1"}}
{"doc":{...},"doc_as_upsert":true}
```

**Chunk size:** 500 documents (1000 bulk lines) — documented in module docstring; caller may override.

**Content-Type:** `application/x-ndjson` with trailing newline.

**Failure policy (v1):** HTTP 401/403/404 on bulk → fail immediately. Per-item errors in 200 bulk response → accumulate; return `BulkResult(succeeded=N, failed=M, errors=[...])`. Smoke CLI treats any failed item as non-zero exit.

### Index mappings (R1-FR-ES-4, R1-FR-ES-6)

Checked-in artifact: `data/elasticsearch/snyk-ado-work-items-mappings.json`

Minimal properties (align with reporting-document-model):

| Path | ES type | Notes |
|------|---------|-------|
| `work_item.id`, `organization`, `project`, `status`, `area_path` | `keyword` | |
| `work_item.title` | `text` | `fields.keyword` subfield |
| `work_item.created_at`, `changed_at`, `closed_at` | `date` | |
| `work_item.days_to_close` | `float` | |
| `tags.raw`, `severity`, `finding_type` | `keyword` | |
| `tags.operator` | `keyword` | |
| `export.run_id` | `keyword` | |
| `export.exported_at` | `date` | |
| `snyk.*` | per R1-FR-DOC-4 | Include in template for future enrich |

**Index create:** `PUT /{index}` with `{ "mappings": { "properties": ... } }` when `auto_create_index` and index missing (`HEAD /{index}` → 404).

**Alternative (documented fallback):** Dev Tools snippet in `CONFIGURATION.md` for operators who prefer manual index setup.

### Public API

```python
class ElasticsearchIngestClient:
    def __init__(
        self,
        *,
        url: str,
        api_key: str | None = None,
        username: str | None = None,
        password: str | None = None,
        transport: HttpTransport | None = None,
    ) -> None: ...

    def ensure_index(self, index_name: str, *, mappings: dict) -> None: ...

    def bulk_upsert_documents(
        self,
        index_name: str,
        documents: Iterable[dict[str, Any]],
        *,
        chunk_size: int = 500,
    ) -> BulkResult: ...

def build_ingest_client_from_env(
    *,
    transport: HttpTransport | None = None,
) -> ElasticsearchIngestClient: ...
```

### CLI: `elasticsearch-smoke index-one` (R1-FR-ES-10)

Mirror `azure-devops-smoke wiql` structure:

```
src/main.py
  elasticsearch-smoke
    index-one [--config PATH]
```

**Behavior:**

- Load config (optional `--config`; default path behavior matches future export conventions)
- Build ingest client from env; fail fast if `ELASTICSEARCH_URL` unset
- When `auto_create_index`, call `ensure_index` with checked-in mappings
- Bulk upsert **one hardcoded** reporting document (normative example from R1-FR-DOC-6)
- Print JSON summary to stdout: `_id`, `index_name`, `succeeded`, `failed`
- Exit `0` on success; errors to stderr without credential material

**Example:**

```bash
export ELASTICSEARCH_URL='https://...'
export ELASTICSEARCH_API_KEY='...'

uv run python src/main.py elasticsearch-smoke index-one \
  --config data/reporting.sample.yaml
```

**Alternative considered:** Standalone `scripts/index_one_doc.py`. Rejected in favor of CLI symmetry with ADO smoke and single entry point (`src/main.py`).

### Testing strategy

| Layer | Cases |
|-------|-------|
| `auth.py` | API key header; basic auth fallback; missing URL raises |
| `bulk.py` | NDJSON line pairs; `_id` derivation; chunk splitting |
| `client.py` | Fake transport: successful bulk; partial item failure; 401 fails fast |
| `mappings.py` | Artifact loads; required date/keyword fields present |
| `config/loader` | Sample YAML exposes `index_name`; defaults when section absent |
| `elasticsearch_smoke` | CLI dispatches; missing URL exits non-zero; fake transport success path |

Use `FakeTransport` recording method, URL, headers (assert no secrets in logs), body — same style as `tests/integrations/azure_devops_reporting/test_http.py`.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| ES 8.x bulk response shape | Parse `items[]` defensively; fixture from ES docs |
| Dynamic mapping on partial index create | Always ship explicit mappings artifact |
| Duplicated HTTP transport | Copy ADO pattern for v1; extract shared module later if needed |
| Hardcoded smoke document drifts from schema | Use R1-FR-DOC-6 normative example; test asserts required keys |

## Migration Plan

Not applicable — greenfield ingest module. Operators create index manually or rely on `auto_create_index` on first smoke run.

## Open Questions

None blocking implementation.
