## Context

Reporting export is a **batch, exit-on-complete** job — same shape as upstream [snyk-azure-boards-integration](https://github.com/snyk-ps/snyk-azure-boards-integration) sync:

```
Cron (every 2h) → Container App Job → export → exit 0|1
                    ↑ secrets (env)       ↑ NDJSON stdout → Log Analytics
                    ↑ /config/reporting.yaml (Azure Files)
```

Existing pieces:

| Piece | Location | Status |
|-------|----------|--------|
| Config default path | `src/config/paths.py` → `/config/reporting.yaml` | Done |
| Export command + observability | `src/commands/export.py`, `export_summary` NDJSON | Done |
| Multi-stage Dockerfile | uv builder, slim runtime, uid 999, `PYTHONUNBUFFERED=1` | CMD needs update |
| Operator runbook | `README.md` § Deployment | Stub only |
| Reference template | `data/context/README.md` | Sync-repo ACA walkthrough to adapt |

## Goals / Non-Goals

**Goals:**

- Production-ready container default: ENTRYPOINT + CMD runs `export` against mounted config
- Portal-first Azure Container App Job runbook (adapt `data/context/README.md` § Deployment)
- `docker run` parity for local smoke before ACA deploy
- Document **every 2 hours** as recommended schedule (export runs are fast)
- Keep production scope dead simple: full YAML config only; no ACA CLI scope overrides

**Non-Goals:**

- Delete `.github/template` or add `VERSION` (GHCR bootstrap stays in CONTRIBUTING.md as existing guidance)
- Bicep / Terraform / ARM modules
- Elastic Cloud IP allowlist, private link, or serverless-specific networking notes
- Production use of `--org` / `--project` on the job container (dev/smoke only; defer phased-rollout docs)
- Application code changes
- Kibana alert rule IaC

## Decisions

### Dockerfile ENTRYPOINT + CMD

Mirror the sync-repo pattern:

```dockerfile
ENTRYPOINT ["python", "src/main.py"]
CMD ["export", "--config", "/config/reporting.yaml"]
```

**Rationale:** ENTRYPOINT keeps `python src/main.py` fixed; operators override args for smoke subcommands (`docker run … azure-devops-smoke wiql …`) without replacing the entrypoint. CMD provides the scheduled-job default.

**Alternative considered:** Single `CMD ["python", "src/main.py", "export", …]` — rejected because overriding smoke commands requires replacing the entire CMD including the Python invocation.

Do **not** COPY sample config into the image; operators mount policy at runtime.

### Config mount path

Standardize on `/config/reporting.yaml` everywhere:

- `DEFAULT_CONTAINER_CONFIG_PATH` in code
- Dockerfile CMD `--config` argument
- Azure Files walkthrough: upload `reporting.yaml` to share root, mount share at `/config`

Matches existing CONFIGURATION.md and R1-FR-CFG-11.

### README structure

Adapt `data/context/README.md` sections:

| Sync repo section | Reporting adaptation |
|-------------------|---------------------|
| `sync --config /config/config.yaml` | `export --config /config/reporting.yaml` |
| Secrets: `SNYK_TOKEN`, `AZURE_DEVOPS_PAT` | `AZURE_DEVOPS_PAT`, `ELASTICSEARCH_URL`, `ELASTICSEARCH_API_KEY` |
| `sync_summary` / `sync_duration_seconds` | `export_summary` / duration + `documents_written` |
| Azure Table + managed identity | **Omit** (stateless export) |
| Outbound: Snyk + dev.azure.com + Table | Outbound: dev.azure.com + Elasticsearch |
| Daily 24h schedule | **Every 2 hours** (`0 */2 * * *` UTC example) |

Add dev vs deployment quick-start split at top of README (currently missing).

### Schedule cadence

Recommend **every 2 hours** because export runs complete quickly and operators benefit from fresher Kibana data without heavy API load. Document example cron `0 */2 * * *` (UTC). Note that operators can adjust cadence; stress-test that runs finish before the next trigger to avoid overlap.

### Scope overrides

Production jobs use image defaults only — full config scope from mounted YAML. `--org` / `--project` / `--filter-tag` remain documented for local development and smoke tests in CONFIGURATION.md; README deployment section does not describe ACA arg overrides.

### GHCR publishing

No change to `.github/template` or `VERSION` in this change. CONTRIBUTING.md already documents the bootstrap flow; update Dockerfile table and add export `docker run` example only.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Default CMD hides `--help` on bare `docker run` | Document: `docker run … <image> --help` overrides CMD args via ENTRYPOINT |
| ES cluster unreachable from ACA egress | README notes outbound HTTPS requirement; Elastic Cloud specifics deferred |
| 30-minute default replica timeout | Document tuning from `export_summary`; export is fast but large tenants may need increase |
| Config file naming confusion (`config.yaml` vs `reporting.yaml`) | Consistent `reporting.yaml` everywhere in docs and walkthrough |
| 2h schedule overlap if export runs long | Document: tune cron or timeout after observing `export_summary` duration |

## Migration Plan

1. Merge this change; build/push new image tag when GHCR is enabled (separate bootstrap).
2. Operators update Container App Job to new image tag (ENTRYPOINT/CMD change is backward-compatible if they already passed explicit args).
3. No data migration; stateless export.

**Rollback:** Revert to previous image tag; no persistent state in the job itself.

## Open Questions

None — scope locked in proposal review.
