# Configuration reference

Operator reference for configuration files, environment variables, and CLI flags. For installation, usage, and deployment, see the [README](README.md). For layout, tests, OpenSpec, and CI/Docker details, see **[CONTRIBUTING.md](CONTRIBUTING.md)**.

## Precedence

For smoke and future export commands, resolution order is:

1. Built-in defaults (for example `filter_tag: Snyk`)
2. Configuration file (`--config` or future `REPORTING_APP_CONFIG`)
3. **CLI arguments** (highest precedence for org/project/filter tag on smoke)

Secrets always come from environment variables only. They are never read from YAML or CLI flags.

## Configuration files

Sample file: **`data/reporting.sample.yaml`**. Copy to a local path such as `data/local.yaml` for development; do not commit secrets or local overrides.

```yaml
azure_devops:
  organizations:
    - name: torstencannell
      filter_tag: Snyk
      projects:
        - snykDemoProject
```

| Key | Type | Default | Role |
| --- | ---- | ------- | ---- |
| `azure_devops.organizations[].name` | string | required | ADO organization |
| `azure_devops.organizations[].filter_tag` | string | `Snyk` | WIQL `[System.Tags] CONTAINS` value |
| `azure_devops.organizations[].projects` | string[] | `[]` | Project allowlist; smoke uses the first entry when `--project` is omitted |

Other sections in the sample (`reporting`, `elasticsearch`) document future export behavior and are not required for ADO smoke today.

## Environment variables

**Secrets** must come from environment variables or your secret store. **Never** commit them in configuration files or source.

| Variable | Required | Role |
| -------- | -------- | ---- |
| **`AZURE_DEVOPS_PAT`** | For ADO client and smoke commands | Azure DevOps personal access token (**secret**; HTTP Basic password with empty username). Fail fast when unset. Never log. |
| **`REPORTING_APP_CONFIG`** | Optional | Default reporting YAML path for future export (not used by smoke unless `--config` is omitted in a later command). |

## CLI flags and parameters

Entry point: **`src/main.py`**.

Run:

```bash
uv run python src/main.py --help
uv run python src/main.py azure-devops-smoke wiql --help
```

### `azure-devops-smoke wiql`

| Flag / parameter | Default | Purpose |
| ---------------- | ------- | ------- |
| `--org` | From config when `--config` is set | ADO organization name |
| `--project` | First configured project when `--config` is set | ADO project to query |
| `--filter-tag` | Config value or `Snyk` | WIQL tag filter |
| `--config` | none | Path to reporting YAML |

## Commands

### Azure DevOps smoke (WIQL)

Read-only WIQL discovery and batch hydration for one org/project. Writes normalized JSON lines to **stdout**:

```bash
export AZURE_DEVOPS_PAT='***'

uv run python src/main.py azure-devops-smoke wiql \
  --org torstencannell \
  --project snykDemoProject \
  --filter-tag Snyk
```

Using the sample config:

```bash
uv run python src/main.py azure-devops-smoke wiql \
  --config data/reporting.sample.yaml \
  --project snykDemoProject
```

Pretty-print JSONL locally:

```bash
uv run python src/main.py azure-devops-smoke wiql \
  --org torstencannell \
  --project snykDemoProject | \
  uv run python src/main.py output --pretty
```

Exit code `0` on success, including when WIQL returns no matches. Errors go to **stderr** without credential material.

### `output`

Read normalized JSONL from stdin or a file and print it again, optionally with `--pretty`.

## Error handling and logging

- Missing or empty **`AZURE_DEVOPS_PAT`** fails before any Azure DevOps HTTP request.
- HTTP **401** and **403** are treated as authentication failures with safe error messages.
- Transient **5xx** and **429** responses retry with bounded exponential backoff.
- Smoke stdout is normalized work item JSONL only; it is not export audit NDJSON.
