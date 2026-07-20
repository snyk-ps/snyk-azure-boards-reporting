## Context

The repository has canonical specs for a read-only Azure DevOps WIT client (`azure-devops-reporting-client`, R1-FR-ADO-1 through R1-FR-ADO-9) and operator YAML shape (`application-config`), but `src/` is still a scaffold with no integration code. Upstream [snyk-azure-boards-integration](https://github.com/snyk-ps/snyk-azure-boards-integration) owns write paths and tag vocabulary; reporting only reads work items tagged for Snyk sync.

This change implements the client and a smoke CLI so operators can verify ADO connectivity and normalized output before Elasticsearch ingest, mapping store enrich, or full export orchestration exist.

## Goals / Non-Goals

**Goals:**

- Implement `AzureDevOpsReportingClient` with list projects, WIQL by filter tag, and work items batch (max 200 IDs per call)
- PAT from `AZURE_DEVOPS_PAT` only; fail fast; no secrets in logs
- Normalize hydrated items to `{ work_item_id, work_item_status, fields }`
- Ship `data/reporting.sample.yaml` with configurable `filter_tag`
- Provide `azure-devops-smoke wiql` subcommand that emits normalized JSONL on stdout
- Unit-test all public/protected surfaces with mocked HTTP

**Non-Goals:**

- Elasticsearch bulk ingest or index management
- Mapping store read/join
- Full `export` orchestration (`work-item-export-lifecycle`)
- Reporting document model transform (tag parsing, closure fallback)
- Kibana dashboards
- Export-run NDJSON audit logging on smoke stdout (future export concern)

## Decisions

### Package layout (R1-FR-ADO-1)

```
src/
  main.py
  commands/
    azure_devops_smoke.py
    output.py                    # optional local JSONL viewer
  config/
    loader.py
  integrations/
    azure_devops_reporting/
      auth.py
      client.py
      models.py
      http.py
data/
  reporting.sample.yaml
tests/
  integrations/azure_devops_reporting/
  commands/
  config/
```

Integration modules MUST NOT read YAML or PAT from disk. Callers pass `organization`, `project`, and `filter_tag` explicitly.

**Alternative considered:** Single monolithic `client.py`. Rejected to keep auth/HTTP testable in isolation.

### HTTP client: stdlib only

Use `urllib.request` (or `http.client`) with a thin wrapper for retries and safe error messages. No `requests` dependency.

**Alternative considered:** `httpx`/`requests`. Rejected per project guidelines (stdlib when possible).

### API version and endpoints (R1-FR-ADO-3)

All WIT calls use `api-version=7.1`:

| Operation | Method | URL |
|-----------|--------|-----|
| List projects | GET | `https://dev.azure.com/{org}/_apis/projects` |
| WIQL | POST | `https://dev.azure.com/{org}/{project}/_apis/wit/wiql` |
| Batch hydrate | POST | `https://dev.azure.com/{org}/{project}/_apis/wit/workitemsbatch` |

### List projects pagination (R1-FR-ADO-4)

Follow ADO continuation semantics for API 7.1: loop using continuation token until all pages are retrieved. Return normalized `{ id, name }` records.

### WIQL and filter tag (R1-FR-ADO-5)

```sql
SELECT [System.Id]
FROM WorkItems
WHERE [System.Tags] CONTAINS '{filter_tag}'
```

Reject or escape `filter_tag` values containing unescaped `'` to avoid WIQL injection. Default tag `Snyk` when not supplied.

### Batch hydration and chunking (R1-FR-ADO-6)

Request minimum field set from canonical spec. Enforce `len(ids) <= 200` before HTTP. Smoke CLI chunks WIQL results into 200-ID batches.

Future export orchestrator will reuse the same chunking helper.

### Normalization (R1-FR-ADO-7)

Map API response to:

```json
{
  "work_item_id": 1001,
  "work_item_status": "Done",
  "fields": { "...": "..." }
}
```

Missing optional date fields remain absent or null in `fields`; batch MUST NOT fail.

### Auth (R1-FR-ADO-2)

Read `AZURE_DEVOPS_PAT` at client construction. HTTP Basic with empty username and PAT as password. Raise configuration error before any HTTP when unset/empty.

### Error handling and retries (R1-FR-ADO-9)

- 401/403 → classified authentication error; no credential echo
- 5xx / rate limit → bounded retry (e.g. 3 attempts, exponential backoff starting at 1s)
- Log safe targets only: host + path template, never Authorization

### Smoke CLI (R1-FR-ADO-10)

Dedicated subcommand mirroring upstream sync-repo smoke pattern:

```bash
uv run python src/main.py azure-devops-smoke wiql \
  --org torstencannell \
  --project snykDemoProject \
  [--filter-tag Snyk] \
  [--config data/reporting.sample.yaml]
```

Precedence: CLI flags override config; PAT always from environment.

Flow: validate PAT → WIQL → chunk IDs @ 200 → batch hydrate → normalize → `json.dumps(record)` + newline to stdout.

- **Stdout:** normalized work item JSONL (future ES ingest reads this stream)
- **Stderr:** human-readable errors/progress
- Exit 0 on success including zero WIQL matches; non-zero on config/auth/terminal HTTP failure

**Alternative considered:** `export --smoke-wiql` flag. Rejected because full export is deferred and smoke should stay independent.

### Optional `output` subcommand

Read JSONL from stdin or a file; optional `--pretty` for local inspection. Not on the critical path; skip if timeboxed.

### Future pipeline hook

Full export will extend: WIQL → batch → normalize → **reporting document model** → optional mapping enrich → **Elasticsearch bulk**. Document `_id` strategy (org + project + work_item_id) belongs in that future change; smoke JSONL uses client-normalized shape only.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| WIQL string injection via malicious `filter_tag` | Reject/escape single quotes in tag values |
| Large WIQL result sets cause long smoke runs | Document expected runtime; chunking limits batch size to 200 |
| ADO rate limiting on manual smoke | Bounded retry; operator runs smoke sparingly |
| Sample config drift from production shape | Keep sample minimal but valid per R1-FR-CFG-2 |
| Multi-org config with smoke using first org only | Document limitation in CONFIGURATION.md; CLI flags override |

## Migration Plan

Not applicable — greenfield implementation. Operators add `AZURE_DEVOPS_PAT` to environment and run smoke locally. No production deployment in this change.

## Open Questions

- None blocking. Optional `output` subcommand may be dropped if smoke JSONL is sufficient for local testing.
