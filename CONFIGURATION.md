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
| `elasticsearch.index_name` | string | `snyk-ado-work-items` | Target Elasticsearch index for export and smoke |
| `elasticsearch.auto_create_index` | boolean | `true` | Create index with normative mappings when missing |

The sample file also documents `reporting.closed_states` for document transform and future export.

## Environment variables

**Secrets** must come from environment variables or your secret store. **Never** commit them in configuration files or source.

| Variable | Required | Role |
| -------- | -------- | ---- |
| **`AZURE_DEVOPS_PAT`** | For ADO client and smoke commands | Azure DevOps personal access token (**secret**; HTTP Basic password with empty username). Fail fast when unset. Never log. |
| **`ELASTICSEARCH_URL`** | For Elasticsearch smoke and export | Cluster endpoint (for example `https://example.es.cloud:9243`). Fail fast when unset. Never log. |
| **`ELASTICSEARCH_API_KEY`** | For Elasticsearch smoke and export (preferred) | API key auth (**secret**). Sent as `Authorization: ApiKey …`. Never log. |
| **`ELASTICSEARCH_USERNAME`** / **`ELASTICSEARCH_PASSWORD`** | Alternative to API key | Basic auth when API key is not used. Never log. |
| **`REPORTING_APP_CONFIG`** | Optional | Default reporting YAML path for future export (not used by smoke unless `--config` is omitted in a later command). |

## CLI flags and parameters

Entry point: **`src/main.py`**.

Run:

```bash
uv run python src/main.py --help
uv run python src/main.py azure-devops-smoke wiql --help
uv run python src/main.py elasticsearch-smoke index-one --help
```

### `azure-devops-smoke wiql`

| Flag / parameter | Default | Purpose |
| ---------------- | ------- | ------- |
| `--org` | From config when `--config` is set | ADO organization name |
| `--project` | First configured project when `--config` is set | ADO project to query |
| `--filter-tag` | Config value or `Snyk` | WIQL tag filter |
| `--config` | none | Path to reporting YAML |

### `elasticsearch-smoke index-one`

| Flag / parameter | Default | Purpose |
| ---------------- | ------- | ------- |
| `--config` | none | Path to reporting YAML (`elasticsearch.index_name`, `auto_create_index`) |

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

### Elasticsearch smoke (index one)

Indexes one hardcoded reporting document (R1-FR-DOC-6 example) into the configured Elasticsearch index. Requires **`ELASTICSEARCH_URL`** and credentials; does not call Azure DevOps.

```bash
export ELASTICSEARCH_URL='https://***'
export ELASTICSEARCH_API_KEY='***'

uv run python src/main.py elasticsearch-smoke index-one \
  --config data/reporting.sample.yaml
```

On success, prints one JSON summary line to **stdout** with `_id`, `index_name`, `succeeded`, and `failed`.

#### Manual index setup (Dev Tools)

If `elasticsearch.auto_create_index` is `false`, create the index manually before smoke or export. The checked-in mappings artifact is **`data/elasticsearch/snyk-ado-work-items-mappings.json`**. Equivalent Dev Tools snippet:

```json
PUT snyk-ado-work-items
{
  "mappings": {
    "properties": {
      "work_item": {
        "properties": {
          "id": { "type": "keyword" },
          "organization": { "type": "keyword" },
          "project": { "type": "keyword" },
          "title": {
            "type": "text",
            "fields": { "keyword": { "type": "keyword" } }
          },
          "status": { "type": "keyword" },
          "area_path": { "type": "keyword" },
          "created_at": { "type": "date" },
          "changed_at": { "type": "date" },
          "closed_at": { "type": "date" },
          "days_to_close": { "type": "float" }
        }
      },
      "tags": {
        "properties": {
          "raw": { "type": "keyword" },
          "operator": { "type": "keyword" },
          "severity": { "type": "keyword" },
          "finding_type": { "type": "keyword" }
        }
      },
      "export": {
        "properties": {
          "run_id": { "type": "keyword" },
          "exported_at": { "type": "date" }
        }
      }
    }
  }
}
```

For the full mapping including optional `snyk.*` enrich fields, use the checked-in JSON artifact.

### `output`

Read normalized JSONL from stdin or a file and print it again, optionally with `--pretty`.

## Error handling and logging

- Missing or empty **`AZURE_DEVOPS_PAT`** fails before any Azure DevOps HTTP request.
- Missing or empty **`ELASTICSEARCH_URL`** fails before any Elasticsearch HTTP request.
- HTTP **401** and **403** are treated as authentication failures with safe error messages.
- Transient **5xx** and **429** responses retry with bounded exponential backoff.
- Smoke stdout is normalized work item JSONL only; it is not export audit NDJSON.
