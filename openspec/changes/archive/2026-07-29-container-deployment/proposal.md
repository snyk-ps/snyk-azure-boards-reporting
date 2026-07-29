## Why

The export pipeline is implemented (`export` CLI, Elasticsearch ingest, NDJSON observability), but operators cannot run it on a schedule without manual glue. The Dockerfile ships a generic `python src/main.py` entrypoint (prints help and exits), and README/CONFIGURATION lack Azure Container App Job runbook content. Companion repo [snyk-azure-boards-integration](https://github.com/snyk-ps/snyk-azure-boards-integration) documents this deployment model; reporting needs the same operator experience adapted for ADO → Elasticsearch export.

## What Changes

- Update **Dockerfile** to use **ENTRYPOINT + CMD**: `ENTRYPOINT ["python", "src/main.py"]`; default args `export --config /config/reporting.yaml`
- Expand **README.md** deployment section using `data/context/README.md` structure:
  - Dev vs production installation paths
  - Minimum ACA Job requirements (schedule every **2 hours**, CPU/memory, replica timeout, networking)
  - Portal walkthrough: Storage → environment volume → scheduled Container App Job → secrets → `/config` mount → test run
  - Logs/observability (`export_summary`, Log Analytics Kusto examples)
  - Troubleshooting table (config mount, ES auth, PAT scope, timeout)
  - `docker run` example for local container smoke
- Extend **CONFIGURATION.md** with container-deployment cross-links and env-var notes for ACA Jobs
- Update **CONTRIBUTING.md** Dockerfile table (ENTRYPOINT/CMD pattern, export-oriented `docker run` example); keep existing GHCR/template bootstrap notes unchanged
- No application logic changes expected; config path default already implemented in `src/config/paths.py`

**Deferred (not in this change):**

| Deferred | Why |
|----------|-----|
| Enable GHCR releases (delete `.github/template`, add `VERSION`) | Separate repo-bootstrap step; CONTRIBUTING.md already describes it |
| Bicep / Terraform / ARM for ACA | Explicit non-goal; portal runbook only (matches sync repo) |
| ACA `--org` / `--project` args for phased rollout | Production runs full YAML scope; CLI overrides are dev/smoke only |
| Elastic Cloud networking (IP allowlist, private link) | Add when operators need it |
| Kibana alert rule IaC | Document Kusto guidance only |

## Capabilities

### New Capabilities

- `container-deployment`: Operator-facing container image contract and Azure Container App Job deployment requirements (R1-FR-DEP-1 through R1-FR-DEP-6)

### Modified Capabilities

- `application-config`: Container image default config path alignment (R1-FR-CFG-12)
- `observability`: Container log shipping expectations for scheduled jobs (R1-FR-OBS-7)

## Impact

- **Code**: `Dockerfile` ENTRYPOINT/CMD only (no application logic changes expected)
- **Docs**: `README.md` (major expansion), `CONFIGURATION.md`, `CONTRIBUTING.md`
- **Specs**: New `container-deployment`; deltas to `application-config`, `observability`
- **Tests**: Existing `tests/config/test_paths.py` covers default path; manual `docker build`/`docker run` verification in tasks
- **Systems**: Outbound HTTPS to `dev.azure.com` and Elasticsearch; secrets via platform env
