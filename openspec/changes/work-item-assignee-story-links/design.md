## Context

Snyk-tagged ADO work items are typically child items (Bug/Task) linked to a parent via **`System.Parent`**. Assignee lives on **`System.AssignedTo`**. Kibana needs stable keyword/url fields, not raw ADO identity objects.

Current flow: WIQL → batch hydrate (fixed field list) → `build_reporting_document()` → bulk upsert with stable `_id` `{organization}:{project}:{work_item.id}`.

## Goals / Non-Goals

**Goals:**

- Populate assignee display name, work item URL, parent story title, and parent story URL on every exported document
- Keep transform pure (no network); parent titles resolved in export orchestration
- Nullable fields when assignee unassigned or no parent

**Non-Goals:**

- ADO Server / custom host URL configuration
- Parent type filtering (User Story vs Epic vs Feature)
- Mapping store or tag parser changes

## Decisions

### 1. Document field names

| Operator label | Document path | ES type | Source |
|----------------|---------------|---------|--------|
| Assignee | `work_item.assignee` | `keyword` | `System.AssignedTo.displayName`; `null` if unassigned |
| Work Item Link | `work_item.url` | `keyword` | Constructed ADO URL |
| Story Name | `work_item.story_name` | `keyword` | Parent `System.Title` |
| Story Link | `work_item.story_url` | `keyword` | Constructed ADO URL for parent id |

Use `story_url` (not `story_link`) to pair with `story_name` and match `work_item.url` naming.

### 2. ADO URL construction

Default pattern (matches R1-FR-ADO-3):

```
https://dev.azure.com/{organization}/{project}/_workitems/edit/{id}
```

- `organization` from export context
- `project` from `System.TeamProject` (URL-encode path segments via stdlib `urllib.parse.quote`)
- `id` from work item or parent id

Pure helper in `src/reporting/urls.py`.

**Alternative considered:** Store ADO `_links` from API responses — rejected because batch responses do not always include stable edit URLs and construction is deterministic from known scope.

### 3. Parent story resolution

1. Primary batch requests `System.Parent` alongside existing fields.
2. Export runner collects unique non-null parent IDs from the hydrated set.
3. Second batch call(s) in chunks of 200 fetch parent `System.Id` + `System.Title` only.
4. Build `parent_titles: dict[int, str]` passed via extended **`TransformContext`**.

Missing parent row (deleted parent, permission gap) → `story_name` and `story_url` are `null`; export continues (same tolerance as optional closure dates).

**Alternative considered:** Single batch with `$expand=Relations` — rejected because relations do not inline parent titles; a second batch is simpler and reuses existing client code.

### 4. Assignee extraction

When `System.AssignedTo` is a dict, use `displayName`. When absent or empty → `null`. Do not store email/uniqueName in the reporting document (PII minimization).

### 5. Pipeline placement

| Layer | Responsibility |
|-------|----------------|
| `azure-devops-reporting-client` | Extended batch field constants; reuse batch API for parent id set |
| `export/runner.py` | Build parent title map between hydrate and transform |
| `reporting/document.py` | Map fields + URLs using context + optional parent map |
| `elasticsearch-platform` | Update checked-in mappings JSON per R1-FR-ES-4 / R1-FR-ES-9 |

Transform remains network-free (R1-FR-DOC-7 preserved).

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Extra ADO API calls for parents | One additional batch pass per unique parent set; dedupe IDs |
| Parent is not literally a "User Story" | Document as immediate hierarchical parent; label "Story" in Kibana for operator familiarity |
| Existing index lacks new fields | Update explicit mappings artifact; re-export upserts by stable `_id` |

## Migration Plan

1. Deploy code + updated mappings artifact (`data/elasticsearch/snyk-ado-work-items-mappings.json`)
2. Run export (upsert updates existing docs by stable `_id` per R1-FR-ES-3)
3. Refresh Kibana data view field list; add new Discover columns per README

No rollback-specific steps — new fields are additive; omitting them in an older build leaves prior documents unchanged until next export.

## Open Questions

None — defaults locked in this design: immediate parent via `System.Parent`, assignee as display name only, default `dev.azure.com` URL pattern.
