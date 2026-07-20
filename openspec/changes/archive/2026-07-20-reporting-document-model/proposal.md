## Why

Change 0 (`build-ado-reporting-client`) proves ADO read paths and emits thin normalized JSONL. The canonical `reporting-document-model` spec defines the Elasticsearch document shape, but no Python transform exists yet. We need a pure, testable normalization layer before export orchestration or Elasticsearch ingest.

## What Changes

- Implement tag parser for `System.Tags` per `upstream-integration-contract` **`contract_version: 1`**
  - Managed: `Snyk-Severity-{level}`, `Snyk-Type-{suffix}`
  - Operator: all other non-empty tokens after `;` split and trim
- Implement ADO field → reporting document mapping per R1-FR-DOC-1 through R1-FR-DOC-5 (without `snyk` enrich)
- Implement closure date resolution per `work-item-export-lifecycle` R1-FR-EXP-5
- Compute `work_item.days_to_close` as UTC fractional days when both dates are present
- Extend config loader minimally to read `reporting.closed_states` (needed for closure fallback)
- Unit tests using curated fixtures from `data/smoke-wiql.jsonl` plus synthetic edge cases
- Optional tiny dev script: JSONL in → reporting JSONL out (no PAT, no network)

**Deferred (not in this change):**

| Deferred | Why |
|----------|-----|
| Mapping store / `snyk` object (R1-FR-DOC-4) | Optional enrich; transform omits `snyk` |
| Elasticsearch ingest | Later change |
| Full export orchestration | Composes client + this transform later |
| Smoke CLI output shape change | Keep smoke on client-normalized JSONL; dev script proves transform |

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `reporting-document-model`: Add normative pure transform surface requirement (R1-FR-DOC-7)
- `application-config`: Loader SHALL expose `reporting.closed_states` (implements existing R1-FR-CFG-3 subset)

## Impact

- **Code**: New `src/reporting/` package; extend `src/config/loader.py`
- **Tests**: `tests/reporting/` with smoke-derived and synthetic fixtures
- **Data**: Optional `tests/fixtures/reporting/` slices from smoke JSONL (committed, small)
- **Dependencies**: stdlib only; no network or Elasticsearch
