## 1. Path encoding

- [ ] 1.1 Add `encode_ado_path_segment()` helper (in `client.py` or `http.py`)
- [ ] 1.2 Apply encoding in `list_projects`, `query_work_item_ids`, and `get_work_items_batch`

## 2. Tests

- [ ] 2.1 Unit test: org/project with spaces produce `%20` in request URLs (extend `FakeTransport` assertions in `test_client.py` or `test_http.py`)
- [ ] 2.2 Confirm existing client tests still pass for alphanumeric org/project names

## 3. Verification

- [ ] 3.1 `uv run pytest`

## 4. Archive (human)

- [ ] 4.1 Merge **`openspec/specs/`** only when archiving: do **not** copy or merge
      **`openspec/changes/fix-ado-api-path-encoding/specs/*.md`** into **`openspec/specs/`**
      during implementation; run **`openspec archive fix-ado-api-path-encoding`**
      (or project equivalent) to fold deltas into canonical specs.
