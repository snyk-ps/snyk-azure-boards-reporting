# Azure DevOps reporting client (Python)

## Purpose

Define normative behavior for a **read-only** Python client that calls Azure DevOps Work Item Tracking (WIT) REST APIs to **discover**, **query**, and **hydrate** work items for reporting. This capability is distinct from upstream [snyk-azure-boards-integration](https://github.com/snyk-ps/snyk-azure-boards-integration) `azure-devops-client`, which supports create, update, list-by-known-ids, and comments only.

REST paths and default **`api-version=7.1`** align with upstream `openspec/specs/integration-apis/spec.md` § Optional APIs (WIQL, work items batch, list projects).

## Requirements

### Requirement: Python package layout (R1-FR-ADO-1)

HTTP modules for Azure DevOps reporting SHALL live under **`src/integrations/azure_devops_reporting/`**. Argparse subcommands and wiring SHALL live under **`src/commands/`**. Entry point **`src/main.py`** SHALL delegate to `src/commands/` without embedding subcommand logic.

The client SHALL NOT read operator YAML or PATs from disk inside the integration package. Callers pass **`organization`**, **`project`**, and query parameters explicitly.

#### Scenario: Import from application code

- **WHEN** export or test code uses the reporting client
- **THEN** HTTP logic is imported from `integrations.azure_devops_reporting`

---

### Requirement: Authenticated access with PAT from environment (R1-FR-ADO-2)

The client SHALL read the Azure DevOps PAT **only** from **`AZURE_DEVOPS_PAT`** (HTTP Basic, empty username, PAT as password). The client SHALL NOT accept a PAT via CLI flags or YAML. The client SHALL NOT log the PAT or `Authorization` material.

If **`AZURE_DEVOPS_PAT`** is unset or empty, the client SHALL fail before issuing HTTP requests.

#### Scenario: Missing PAT

- **WHEN** export runs without `AZURE_DEVOPS_PAT`
- **THEN** the client SHALL fail with a clear error and SHALL NOT echo secret material

---

### Requirement: Base URL and API version (R1-FR-ADO-3)

Default origin: **`https://dev.azure.com`**. All WIT operations in this capability SHALL use **`api-version=7.1`** unless a test-only override is documented for automated tests.

#### Scenario: Default WIT version

- **WHEN** the client lists projects or runs WIQL with defaults
- **THEN** requests SHALL include `api-version=7.1`

---

### Requirement: List projects (R1-FR-ADO-4)

The client SHALL list team projects for a caller-supplied **`organization`**, handling pagination per Azure DevOps REST semantics, and return normalized project records with at least **`id`** and **`name`**.

When application configuration supplies an explicit project allowlist, the export orchestrator MAY skip full enumeration and use configured names only; this requirement applies when **`projects`** is empty (all projects).

#### Scenario: Paginated project list

- **WHEN** an organization has more projects than one API page returns
- **THEN** the client SHALL retrieve all pages before returning

---

### Requirement: WIQL query by filter tag (R1-FR-ADO-5)

The client SHALL execute WIQL per **`organization`** and **`project`**:

```sql
SELECT [System.Id]
FROM WorkItems
WHERE [System.Tags] CONTAINS '{filter_tag}'
```

HTTP: `POST https://dev.azure.com/{organization}/{project}/_apis/wit/wiql?api-version=7.1`

Body: `{ "query": "<WIQL>" }`

The client SHALL return work item IDs from the WIQL result. **`filter_tag`** is supplied by the caller (default **`Snyk`** per `upstream-integration-contract`).

#### Scenario: WIQL returns matching ids

- **WHEN** WIQL matches work items 1001 and 1002 in project `snykDemoProject`
- **THEN** the client SHALL return both IDs

#### Scenario: WIQL returns no matches

- **WHEN** no work items match the filter tag
- **THEN** the client SHALL return an empty ID list without error

---

### Requirement: Work items batch hydration (R1-FR-ADO-6)

Given up to **200** work item IDs, the client SHALL call **Get work items batch**:

`POST https://dev.azure.com/{organization}/{project}/_apis/wit/workitemsbatch?api-version=7.1`

The client SHALL request at minimum these fields:

| Field |
|-------|
| `System.Id` |
| `System.Title` |
| `System.State` |
| `System.Tags` |
| `System.CreatedDate` |
| `System.ChangedDate` |
| `Microsoft.VSTS.Common.ClosedDate` |
| `Microsoft.VSTS.Common.ResolvedDate` |
| `System.TeamProject` |
| `System.AreaPath` |

If the caller supplies more than **200** IDs in one batch call, the client SHALL fail before HTTP with a clear error. The export orchestrator SHALL chunk larger sets.

#### Scenario: Batch limit enforced

- **WHEN** the caller passes 201 IDs to a single batch call
- **THEN** the client SHALL fail before HTTP

#### Scenario: Missing optional date field

- **WHEN** ADO returns a work item without `ClosedDate`
- **THEN** the normalized record SHALL represent that field as absent (`null`) without failing the batch

---

### Requirement: Normalized work item record (R1-FR-ADO-7)

Each hydrated work item SHALL normalize to:

| Key | Source |
|-----|--------|
| `work_item_id` | `id` |
| `work_item_status` | `fields.System.State` |
| `fields` | Full `fields` object from API |

#### Scenario: Normalize state

- **WHEN** API returns `fields.System.State` = `Done`
- **THEN** `work_item_status` SHALL be `Done`

---

### Requirement: Supported operations boundary (R1-FR-ADO-8)

This client SHALL support **list projects**, **WIQL query**, and **work items batch** only.

This client SHALL **NOT** implement work item create, update, delete, comments, or upstream sync list-by-ids for known mapping IDs (those remain in the sync repository).

#### Scenario: No mutation APIs

- **WHEN** application code imports the reporting client
- **THEN** no public method SHALL perform JSON Patch create or update against WIT

---

### Requirement: Error handling and retries (R1-FR-ADO-9)

The client SHALL classify HTTP **401** and **403** as authentication failures. The client MAY retry transient **5xx** and rate-limit responses with bounded backoff; retry policy SHALL be documented in implementation design.

Failed requests SHALL surface safe error messages without credentials.

#### Scenario: Auth failure

- **WHEN** Azure DevOps returns **401**
- **THEN** the client SHALL raise or return a classified auth error without logging the PAT
