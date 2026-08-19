## Context

Export orchestration in `src/export/runner.py`:

1. Bulk upsert via `ElasticsearchIngestClient.bulk_upsert_documents()`
2. `parse_bulk_response()` returns `BulkResult` with `errors: tuple[BulkItemFailure, ...]`
3. On failure, runner appends raw `BulkItemFailure` objects to `errors: list[str]`
4. `to_export_summary()` passes `result.errors` into `ExportSummary`
5. `emit_export_summary()` → `emit_ndjson_record()` → `json.dumps(record)`

`BulkItemFailure` is a frozen dataclass (`document_id`, `error_type`, `reason`). Python's stdlib JSON encoder does not serialize dataclasses.

Production evidence (2026-08-19): 100-project export, all integration HTTP 200, crash at `audit.py:108`, empty Elasticsearch index, no `export_summary` in stdout.

## Goals / Non-Goals

**Goals:**

- `export_summary` always emits when `run_export()` returns, including when bulk items fail
- Each `errors[]` entry is a plain string safe for NDJSON / Log Analytics
- Tests use real `BulkItemFailure` objects end-to-end

**Non-Goals:**

- Changing `BulkItemFailure` or `BulkResult` models
- Adding a custom JSON encoder for audit logging
- Logging full ES bulk response bodies
- Fixing Elasticsearch ingest or mapping issues (separate investigation)

## Decisions

### Format bulk failures as strings in the runner

In `run_export()`, when iterating `bulk_result.errors`:

```python
errors.append(
    f"{bulk_error.document_id}: {bulk_error.error_type}: {bulk_error.reason}"
)
```

**Rationale:** Matches `TransformError` handling (`str(error)`), matches `ExportSummary.errors: tuple[str, ...]`, and satisfies R1-FR-OBS-3 "Non-secret error summary" without changing the audit schema.

**Alternative considered:** `dataclasses.asdict(bulk_error)` → dict in `errors` — rejected because `ExportSummary` and spec define string summaries; would require type and spec changes.

**Alternative considered:** Custom `BulkItemFailure.__str__` — rejected; explicit format in runner (or a named helper) is clearer and testable.

### Optional helper: `format_bulk_item_failure(failure) -> str`

If extracted, place in `src/integrations/elasticsearch/models.py` or `src/integrations/elasticsearch/bulk.py` next to `BulkItemFailure`. Keeps runner thin and gives tests a single assertion target.

### Preserve bounded error list (max 10)

Existing cap in `run_export()` stays unchanged — only the representation of each entry changes.

### Exit code unchanged

`export` still returns exit code `1` when `export_outcome` is `partial` or `failure`. This fix ensures the summary is emitted **before** exit, not that failed runs exit 0.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Error string format changes later | Lock format in unit test; document as convention not public API |
| Long ES `reason` strings in logs | Already bounded to 10 errors; ES reasons are typically short |
| Regression if new non-string error types added | Type `errors` as `list[str]` strictly; test NDJSON round-trip |

## Migration Plan

Deploy patch release. No config migration. Operators on affected versions (`v1.0.0`, `v1.0.1`) should upgrade and re-run export; optional index delete + re-run remains an operator choice for ES data issues, not required by this fix.

## Open Questions

None.
