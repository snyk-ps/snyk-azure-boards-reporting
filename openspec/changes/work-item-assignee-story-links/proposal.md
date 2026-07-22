## Why

Operators reviewing Snyk findings in Kibana need assignee ownership and direct links to the finding work item and its parent story. The export pipeline and reporting document model today omit assignee, parent story context, and ADO URLs, so Discover cannot show who owns an item or navigate to Azure DevOps without manual ID lookup.

## What Changes

- Request **`System.AssignedTo`** and **`System.Parent`** in ADO batch hydration
- After primary hydrate, batch-fetch parent work items to resolve **story title** (`System.Title` of parent)
- Extend reporting documents with:
  - `work_item.assignee`
  - `work_item.url` (work item link)
  - `work_item.story_name`
  - `work_item.story_url` (story link)
- Update Elasticsearch index mappings for new fields
- Extend Kibana detail table (R1-FR-KIB-2) and README Discover column setup

**Deferred (not in this change):**

| Deferred | Why |
|----------|-----|
| Filter parent by `System.WorkItemType` = User Story only | Start with any hierarchical parent via `System.Parent`; tighten later if operators need it |
| Custom ADO base URL (Server/on-prem) | Default `https://dev.azure.com`; config override is a separate change |
| Kibana saved-object NDJSON in repo | Continue manual README setup per R1-FR-KIB-7 |
| Assignee / story filters on dashboard (R1-FR-KIB-1) | Table columns first; global filters can follow |

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `azure-devops-reporting-client`: Batch field list and parent title lookup (R1-FR-ADO-11)
- `reporting-document-model`: Assignee, URLs, and story fields on `work_item` (R1-FR-DOC-8)
- `work-item-export-lifecycle`: Parent hydration pass before transform (R1-FR-EXP-13)
- `elasticsearch-platform`: Mappings for new `work_item.*` fields (follows R1-FR-ES-4)
- `kibana-reporting`: Extend work item detail table columns (R1-FR-KIB-2 delta)

## Impact

- **Code**: ADO batch fields; export runner parent lookup map; `build_reporting_document()` URL/assignee/story mapping; `data/elasticsearch/snyk-ado-work-items-mappings.json`
- **Tests**: ADO models, document transform, export runner (parent map injection), mapping JSON parity
- **Docs**: README Discover columns; optional CONFIGURATION.md note on story derivation
- **Ops**: Re-export (or full export run) required to backfill new fields on existing documents
