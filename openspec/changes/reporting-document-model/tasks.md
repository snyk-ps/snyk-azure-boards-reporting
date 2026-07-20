## 1. Config (closure fallback input)

- [ ] 1.1 Extend `ReportingAppConfig` / `load_config` with `closed_states` (default `[Closed, Done]`) per R1-FR-CFG-3
- [ ] 1.2 Unit tests for `data/reporting.sample.yaml` and default when `reporting` section absent

## 2. Tag parser (R1-FR-DOC-3, upstream contract v1)

- [ ] 2.1 Implement `parse_system_tags()` in `src/reporting/tags.py`
- [ ] 2.2 Unit tests: empty/missing tags, operator-only, managed tags, `TestOverride`, whitespace trimming

## 3. Dates and closure (R1-FR-EXP-5, R1-FR-DOC-2)

- [ ] 3.1 Implement `parse_ado_datetime()` and `compute_days_to_close()` in `src/reporting/dates.py`
- [ ] 3.2 Implement `resolve_closed_at()` in `src/reporting/closure.py`
- [ ] 3.3 Unit tests: ClosedDate precedence, ResolvedDate, closed-state ChangedDate fallback, active nulls

## 4. Document builder (R1-FR-DOC-1, 2, 3, 5, 7)

- [ ] 4.1 Define `TransformContext`, `TransformError`, and output types in `src/reporting/models.py`
- [ ] 4.2 Implement `build_reporting_document()` (and optional batch helper) in `src/reporting/document.py`
- [ ] 4.3 Golden tests for smoke fixtures: ids **1** (operator-only), **9** (closed + days), **113** (managed tags + active)
- [ ] 4.4 Parameterized smoke sweep over `data/smoke-wiql.jsonl` — assert required keys, no exceptions

## 5. Dev ergonomics

- [ ] 5.1 Add `scripts/transform_jsonl.py` — normalized JSONL in, reporting JSONL out (no network)

## 6. Archive prep

- [ ] 6.1 Merge `openspec/specs/` only when archiving: do **not** copy or merge `openspec/changes/reporting-document-model/specs/*.md` into `openspec/specs/` during implementation; run `openspec archive reporting-document-model` when complete
