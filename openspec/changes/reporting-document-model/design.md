## Context

Pipeline position:

```
ADO batch → normalize_work_item() → build_reporting_document() → (future) ES bulk
```

Change 0 output (`NormalizedWorkItem` from `integrations.azure_devops_reporting.models`):

```json
{ "work_item_id": 113, "work_item_status": "To Do", "fields": { ... } }
```

Target output (R1-FR-DOC-1 through R1-FR-DOC-5, no `snyk`):

```json
{ "work_item": { ... }, "tags": { ... }, "export": { ... } }
```

Canonical field rules live in `openspec/specs/reporting-document-model/spec.md`. Closure precedence lives in `work-item-export-lifecycle` R1-FR-EXP-5. Tag vocabulary aligns with `upstream-integration-contract` **`contract_version: 1`**.

Fixture note: `data/smoke-wiql.jsonl` has 655 normalized rows (638 active, 16 closed with `ClosedDate`, no `ResolvedDate`). Closure fallback steps 2–3 require synthetic unit tests in addition to smoke rows.

## Goals / Non-Goals

**Goals:**

- Deterministic, side-effect-free transform (no network, no secrets, no ES)
- Stable JSON values for the same input and transform context
- Test coverage from real ADO-shaped fixtures plus synthetic edge cases
- Minimal config loader extension for `reporting.closed_states`

**Non-Goals:**

- HTTP, PAT, WIQL, mapping store join, Elasticsearch
- Changing `azure-devops-smoke wiql` stdout format
- Full export orchestration or document `_id` strategy

## Decisions

### Module layout

```
src/reporting/
  tags.py       # parse_system_tags(raw: str) -> TagsParsed
  closure.py    # resolve_closed_at(fields, closed_states) -> str | None
  dates.py      # parse_ado_datetime, compute_days_to_close
  document.py   # build_reporting_document(...)
  models.py     # TransformContext, output TypedDicts
```

Keeps transform logic separate from ADO HTTP client and future export orchestration.

### Input shape: NormalizedWorkItem, not raw batch envelope

**Decision:** Accept `NormalizedWorkItem` plus `TransformContext`, not raw ADO `{ value: [...] }` batch JSON.

**Rationale:** Client already normalizes API payloads; transform stays independent of ADO response metadata (revision, URL, etc.).

**Alternative considered:** Accept raw batch dict and normalize internally. Rejected to avoid duplicating `normalize_work_item()`.

### Public API

```python
@dataclass(frozen=True)
class TransformContext:
    organization: str
    run_id: str
    exported_at: datetime  # UTC
    closed_states: frozenset[str]

def build_reporting_document(
    item: NormalizedWorkItem,
    *,
    context: TransformContext,
) -> dict[str, Any]:
    ...
```

Optional batch helper:

```python
def build_reporting_documents(
    items: Iterable[NormalizedWorkItem],
    *,
    context: TransformContext,
) -> list[dict[str, Any]]:
    ...
```

### Tag parsing

Algorithm (R1-FR-DOC-3, R1-FR-UP-3, R1-FR-UP-4):

1. `raw = fields.get("System.Tags") or ""` (preserve in `tags.raw`)
2. Split on `;`, strip each token, drop empties
3. For each token:
   - starts with `Snyk-Severity-` → set `severity` to suffix
   - starts with `Snyk-Type-` → set `finding_type` to suffix
   - else → append to `tags.operator` (preserve ADO order)
4. If multiple managed tags of the same kind (invalid upstream data): **last token wins**

Example (smoke item 113):

```
"Snyk; Snyk-Severity-critical; Snyk-Type-open_source; TestOverride"
→ operator: ["Snyk", "TestOverride"], severity: "critical", finding_type: "open_source"
```

### Work item field mapping

| Output field | Source / rule |
|--------------|---------------|
| `work_item.id` | `str(work_item_id)` — ES keyword |
| `work_item.organization` | `context.organization` |
| `work_item.project` | `fields["System.TeamProject"]` |
| `work_item.title` | `fields["System.Title"]` |
| `work_item.status` | `fields["System.State"]` |
| `work_item.area_path` | `fields.get("System.AreaPath")` or `""` |
| `work_item.created_at` | normalize `System.CreatedDate` to UTC ISO-8601 `...Z` |
| `work_item.changed_at` | normalize `System.ChangedDate` |
| `work_item.closed_at` | closure precedence (below) |
| `work_item.days_to_close` | computed (below) |

Missing required ADO fields (`System.State`, `System.CreatedDate`, `System.TeamProject`, `System.Title`): raise `TransformError` with work item id.

### Closure date precedence (R1-FR-EXP-5)

1. `Microsoft.VSTS.Common.ClosedDate`
2. `Microsoft.VSTS.Common.ResolvedDate`
3. If `System.State in closed_states` → `System.ChangedDate`
4. Else `null`

`closed_states` from config; `data/reporting.sample.yaml` uses `[Done]`.

### days_to_close

When both `created_at` and `closed_at` are non-null:

```
days_to_close = round((closed_at - created_at).total_seconds() / 86400.0, 2)
```

When either date is null → `days_to_close = null`. All date math in UTC.

### Dev script (optional)

```
scripts/transform_jsonl.py
  --input data/smoke-wiql.jsonl
  --org test-org
  --run-id dev-run
  [--closed-states Done]
```

Reads normalized JSONL, writes reporting JSONL to stdout. Satisfies exit criteria without wiring a new `main.py` subcommand.

**Alternative considered:** New CLI subcommand in `main.py`. Deferred; pytest + optional script is enough for Change 1.

### Testing strategy

| Layer | Cases |
|-------|-------|
| `tags.py` | empty/missing tags; operator-only; full managed; `TestOverride`; duplicate managed (synthetic) |
| `closure.py` | ClosedDate; ResolvedDate only; closed state + ChangedDate fallback; active item |
| `document.py` | golden docs for smoke ids **1**, **9**, **113** |
| Smoke sweep | Parameterized test over `data/smoke-wiql.jsonl` — assert schema keys, no exception |

Fixtures: small committed JSON under `tests/fixtures/reporting/` (representative smoke lines + synthetic closure rows).

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| ADO datetime format variance | Single `parse_ado_datetime()` with tests for `...Z` and fractional seconds |
| Config loader scope creep | Only `closed_states` + defaults; defer full reporting config object |
| `work_item.id` int vs str | Always stringify in output |
| Smoke data lacks ResolvedDate / fallback rows | Synthetic unit tests for full closure chain |
| Duplicate managed tags in the wild | Last-wins rule; document in tests |

## Migration Plan

Not applicable — greenfield transform module. No production deployment in this change. Future export orchestration will call `build_reporting_document()` after client normalization.

## Open Questions

None blocking implementation. Dev script is optional if pytest-only workflow is preferred at apply time.
