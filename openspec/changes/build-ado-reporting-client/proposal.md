## Why

The reporting repository defines normative behavior for a read-only Azure DevOps WIT client (`azure-devops-reporting-client`) but has no implementation yet. We need a working client and smoke CLI to prove PAT authentication, WIQL discovery, batch hydration, and normalization against a real organization before Elasticsearch ingest or full export orchestration.

## What Changes

- Implement Python ADO reporting client under `src/integrations/azure_devops_reporting/` per R1-FR-ADO-1 through R1-FR-ADO-9
- PAT auth from `AZURE_DEVOPS_PAT` only — fail fast when missing; never log secrets
- List projects (paginated) for one organization
- WIQL query by configurable filter tag (`[System.Tags] CONTAINS '{filter_tag}'`)
- Work items batch hydration with 200-ID limit enforced per HTTP call; caller chunks larger sets
- Thin normalized record: `work_item_id`, `work_item_status`, `fields`
- Sample operator config at `data/reporting.sample.yaml` with `filter_tag` and example org/project
- `azure-devops-smoke wiql` CLI subcommand (mirror upstream sync-repo smoke pattern): WIQL → batch → normalize → JSON lines on stdout
- Optional `output` CLI helper for local JSONL inspection (pretty-print)
- Unit tests for all public/protected client and command surfaces

**Deferred (not in this change):**

| Deferred | Why |
|----------|-----|
| Elasticsearch ingest | Client + smoke prove ADO side first |
| Mapping store join | Optional enrich; not needed to read work items |
| Full `export` orchestration | Build after client methods are unit-tested |
| Kibana | v2 |
| Reporting document model transform | Smoke emits client-normalized records only |

## Capabilities

### New Capabilities

None. This change implements existing capabilities; no new capability folders.

### Modified Capabilities

- `azure-devops-reporting-client`: Add smoke WIQL CLI requirement (R1-FR-ADO-10) for local ADO verification without Elasticsearch
- `application-config`: Add committed sample config under `data/` (R1-FR-CFG-8)

## Impact

- **Code**: New packages under `src/integrations/azure_devops_reporting/`, `src/config/`, `src/commands/`; wire subcommands in `src/main.py`
- **Tests**: New unit tests under `tests/integrations/azure_devops_reporting/` and `tests/commands/`
- **Data**: New `data/reporting.sample.yaml` (no secrets)
- **Docs**: Update `CONFIGURATION.md` with `AZURE_DEVOPS_PAT`, sample config, and smoke command
- **Dependencies**: Prefer stdlib HTTP; no Elasticsearch or mapping store dependencies
- **Systems**: Read-only calls to Azure DevOps WIT REST API (`api-version=7.1`); stdout JSONL is the intermediate artifact future export/ES ingest will consume
