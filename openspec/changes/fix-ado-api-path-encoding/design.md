## Context

ADO WIT endpoints documented in R1-FR-ADO-4 through R1-FR-ADO-6 use paths like:

```
https://dev.azure.com/{organization}/{project}/_apis/wit/wiql?api-version=7.1
```

Azure DevOps expects path segments to be URL-encoded. A project named `Project Name` must appear as `Project%20Name` in the path.

`AzureDevOpsHttpClient._build_url()` only URL-encodes **query** parameters (`api-version`, `$top`, etc.) via `urllib.parse.urlencode`. Path segments are assembled in `AzureDevOpsReportingClient` without encoding.

`src/reporting/urls.py` already uses `quote(segment, safe="")` for work item edit links (added in the assignee/story-links change).

## Goals / Non-Goals

**Goals:**

- All ADO WIT REST requests from the reporting client use correctly encoded org/project path segments
- Encoding behavior matches `build_ado_work_item_url`
- Unit tests lock encoding for names with spaces

**Non-Goals:**

- Deduplicating URL construction between API paths and reporting URLs (acceptable follow-up)
- Encoding work item IDs or API resource suffixes (`_apis/...`) — only caller-supplied org/project names

## Decisions

### Encode path segments in the reporting client before HTTP

Add a small helper (either in `client.py` or `http.py`):

```python
from urllib.parse import quote

def encode_ado_path_segment(value: str) -> str:
    return quote(value, safe="")
```

Use it when building paths in `list_projects`, `query_work_item_ids`, and `get_work_items_batch`:

| Method | Path pattern |
|--------|----------------|
| `list_projects` | `/{quote(org)}/_apis/projects` |
| `query_work_item_ids` | `/{quote(org)}/{quote(proj)}/_apis/wit/wiql` |
| `get_work_items_batch` | `/{quote(org)}/{quote(proj)}/_apis/wit/workitemsbatch` |

**Alternative considered:** Encode inside `AzureDevOpsHttpClient._build_url()` by parsing path templates — rejected because the HTTP layer should not guess which segments are user-supplied vs fixed API suffixes.

**Alternative considered:** Double-encoding if callers pass pre-encoded names — rejected; callers always pass raw ADO names from config or API responses. Document that paths must receive decoded names.

### Logging / safe_target

`safe_target` logs the path as sent (encoded). That is acceptable and avoids leaking unencoded special characters in log aggregation.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Regression for simple alphanumeric org/project names | `quote("snykDemoProject")` → unchanged; existing tests still pass |
| Special chars beyond spaces (`&`, `#`, `/`) | `quote(..., safe="")` handles standard path segment encoding |

## Migration Plan

No migration required. Deploy the fix; existing configs with URL-safe names behave identically. Orgs/projects with spaces in names start working immediately.

## Open Questions

None.
