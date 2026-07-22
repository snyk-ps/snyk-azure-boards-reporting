## 1. Config (R1-FR-CFG-4)

- [x] 1.1 Add `ElasticsearchConfig` to `ReportingAppConfig`; parse `elasticsearch.index_name` (default `snyk-ado-work-items`) and `auto_create_index` (default `true`)
- [x] 1.2 Unit tests: sample YAML, defaults when section absent, invalid types fail fast

## 2. Elasticsearch auth and errors (R1-FR-ES-1)

- [x] 2.1 Implement `build_ingest_client_from_env()` and auth header builder in `src/integrations/elasticsearch/auth.py`
- [x] 2.2 Fail fast when `ELASTICSEARCH_URL` unset; never log credentials
- [x] 2.3 Unit tests for API key, basic auth fallback, missing URL

## 3. HTTP transport (stdlib)

- [x] 3.1 Implement `HttpTransport` protocol and `UrllibTransport` in `src/integrations/elasticsearch/http.py` (mirror ADO client pattern)
- [x] 3.2 Unit tests with fake transport helper for injectable requests

## 4. Index mappings artifact (R1-FR-ES-4, R1-FR-ES-9)

- [x] 4.1 Add `data/elasticsearch/snyk-ado-work-items-mappings.json` per reporting-document-model field types
- [x] 4.2 Implement `load_index_mappings()` in `mappings.py` with unit test asserting key field types (`date`, `keyword`, `text`+subfield)

## 5. Bulk upsert client (R1-FR-ES-3, R1-FR-ES-5, R1-FR-ES-8)

- [x] 5.1 Implement `document_id()` and NDJSON bulk payload builder (`update` + `doc_as_upsert`) in `bulk.py`
- [x] 5.2 Implement `ElasticsearchIngestClient.bulk_upsert_documents()` with chunking (default 500) in `client.py`
- [x] 5.3 Parse bulk response; return `BulkResult` with success/failure counts; fail fast on HTTP 401/403/404
- [x] 5.4 Unit tests with HTTP fake: happy path, partial item failure, auth failure, stable `_id` format

## 6. Index setup (R1-FR-ES-6)

- [x] 6.1 Implement `ensure_index()` (HEAD + PUT with mappings when missing and `auto_create_index`)
- [x] 6.2 Document Dev Tools fallback snippet in `CONFIGURATION.md` for manual index creation
- [x] 6.3 Unit test: fake transport sees PUT with mappings when index absent

## 7. CLI smoke command (R1-FR-ES-10)

- [x] 7.1 Implement `src/commands/elasticsearch_smoke.py` with `elasticsearch-smoke index-one` subcommand
- [x] 7.2 Wire subcommand in `src/main.py`; hardcoded R1-FR-DOC-6 example document; JSON summary on stdout
- [x] 7.3 Unit tests in `tests/commands/test_elasticsearch_smoke.py` (missing URL, success with fake transport)

## 8. Documentation

- [x] 8.1 Update `CONFIGURATION.md` with `ELASTICSEARCH_URL`, `ELASTICSEARCH_API_KEY`, and `elasticsearch-smoke index-one` example

## 9. Archive prep

- [x] 9.1 Merge `openspec/specs/` only when archiving: do **not** copy or merge `openspec/changes/elasticsearch-platform/specs/*.md` into `openspec/specs/` during implementation; run `openspec archive elasticsearch-platform` when complete
