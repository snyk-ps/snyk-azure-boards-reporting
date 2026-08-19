## Why

Azure DevOps REST paths treat `{organization}` and `{project}` as URL path segments. Names containing spaces or other reserved characters (for example `Project Name`) must be percent-encoded. The reporting client currently interpolates org and project names verbatim into request paths, causing HTTP failures (404 or similar) for organizations or projects whose names are not URL-safe.

Reporting document URLs already encode path segments correctly via `build_ado_work_item_url()`; the HTTP client does not.

## What Changes

- Percent-encode **`organization`** and **`project`** path segments on all Azure DevOps WIT REST calls:
  - `GET /{organization}/_apis/projects`
  - `POST /{organization}/{project}/_apis/wit/wiql`
  - `POST /{organization}/{project}/_apis/wit/workitemsbatch`
- Use stdlib `urllib.parse.quote(..., safe="")` (same rule as `src/reporting/urls.py`)
- Add unit tests asserting encoded URLs for org/project names with spaces

**Out of scope:**

| Out of scope | Why |
|--------------|-----|
| Custom ADO base URL / on-prem host | Separate change |
| Refactoring `build_ado_work_item_url` to share a helper | Optional follow-up; not required to fix API calls |
| Elasticsearch, export orchestration, config | Unaffected |

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `azure-devops-reporting-client`: Clarify and enforce URL-encoded path segments on REST requests (R1-FR-ADO-12)

## Impact

- **Code**: `src/integrations/azure_devops_reporting/client.py` (and optionally a small shared path helper)
- **Tests**: `tests/integrations/azure_devops_reporting/test_client.py` and/or `test_http.py`
- **Docs**: None required
- **Ops**: Fixes export and `azure-devops-smoke wiql` for orgs/projects with spaces in names; no config migration
