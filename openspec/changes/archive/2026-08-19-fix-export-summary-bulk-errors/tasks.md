## 1. Fix bulk error serialization

- [x] 1.1 In `src/export/runner.py`, format each `BulkItemFailure` as a string before appending to `errors` (e.g. `{document_id}: {error_type}: {reason}`)
- [x] 1.2 Optionally extract `format_bulk_item_failure()` helper next to `BulkItemFailure` if it improves testability

## 2. Tests

- [x] 2.1 Update `tests/export/test_runner.py`: fake ES client returns `BulkResult` with real `BulkItemFailure` instances; assert `result.errors` are strings
- [x] 2.2 Add test: `to_export_summary()` + `emit_export_summary()` with bulk failure strings produces valid JSON (extend `tests/observability/test_audit.py`)
- [x] 2.3 Confirm existing export/runner partial-failure tests still pass

## 3. Verification

- [x] 3.1 `uv run pytest`
- [x] 3.2 Manual sanity: simulate partial bulk failure path and confirm no `TypeError` on summary emit

## 4. Archive (human)

- [x] 4.1 Merge **`openspec/specs/`** only when archiving: do **not** copy or merge
      **`openspec/changes/fix-export-summary-bulk-errors/specs/*.md`** into **`openspec/specs/`**
      during implementation; run **`openspec archive fix-export-summary-bulk-errors`**
      (or project equivalent) to fold deltas into canonical specs.
