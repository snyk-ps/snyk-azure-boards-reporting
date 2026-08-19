## Why

When Elasticsearch bulk ingest returns per-item failures, `export` accumulates `BulkItemFailure` dataclass instances in the run result's `errors` list. `emit_export_summary()` then calls `json.dumps()` on those values, which raises:

`TypeError: Object of type BulkItemFailure is not JSON serializable`

The export run crashes **after** ADO discovery and ES bulk calls complete, so operators see a failed Container App job and **no `export_summary` line** — even though the underlying issue may be partial or total bulk rejection. This blocked diagnosis of a production incident where 100 projects were processed but zero documents appeared in Elasticsearch.

Transform errors are already converted with `str(error)` before append; bulk errors are not.

## What Changes

- Serialize each `BulkItemFailure` to a **string** before appending to the export run `errors` list (consistent with `ExportSummary.errors: tuple[str, ...]` and R1-FR-OBS-3)
- Recommended format: `{document_id}: {error_type}: {reason}`
- Add unit tests using real `BulkItemFailure` objects (not plain strings) through `run_export` → `to_export_summary` → `emit_export_summary`
- Fix existing `tests/export/test_runner.py` fake bulk results to use `BulkItemFailure` instances so the gap that allowed this regression is closed

**Out of scope:**

| Out of scope | Why |
|--------------|-----|
| Fixing Elasticsearch ingest / mapping issues | Separate investigation; this change exposes errors, does not fix root cause |
| Structured `errors` as JSON objects in `export_summary` | Spec and `ExportSummary` already define string summaries; avoid schema churn |
| Catching `TypeError` generically in `export.py` | Treat the symptom, not the cause |
| Operator runbook for delete-index-and-re-run | Optional follow-up doc; not required to ship the bug fix |

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `observability`: Clarify that `export_summary.errors` entries MUST be JSON-serializable strings; bulk failures SHALL NOT prevent summary emission (R1-FR-OBS-1, R1-FR-OBS-3, R1-FR-OBS-6)
- `work-item-export-lifecycle`: Export orchestration SHALL record bulk failures as string summaries and always emit summary at completion (R1-FR-EXP-12, cross-ref R1-FR-OBS-3)

## Impact

- **Code**: `src/export/runner.py` (primary fix); optional small helper in `src/integrations/elasticsearch/` or `src/export/` for formatting
- **Tests**: `tests/export/test_runner.py`, `tests/observability/test_audit.py`; possibly `tests/commands/test_export.py`
- **Ops**: Deploy as patch release (e.g. `v1.0.2`); operators can then read `export_summary.errors` in Log Analytics to diagnose ES bulk rejections
- **Docs**: None required
