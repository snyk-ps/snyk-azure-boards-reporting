# Snyk Azure Boards Reporting

Export Snyk-tagged Azure DevOps work items to Elasticsearch for Kibana reporting. The application reads work items via WIQL, normalizes them into reporting documents, and bulk-upserts them into a configured Elasticsearch index. Azure DevOps access is read-only.

## Table of contents

- [Installation and setup](#installation-and-setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Kibana setup](#kibana-setup)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Deployment](#deployment)
- [More documentation](#more-documentation)

## Installation and setup

### Prerequisites

- **Python** 3.12+ and **[uv](https://docs.astral.sh/uv/getting-started/installation/)**
- **Azure DevOps** personal access token with read access to work items
- **Elasticsearch** cluster (Elastic Cloud or self-hosted) with API key or basic auth

### Development / local installation

```bash
uv sync --dev
```

Copy `data/reporting.sample.yaml` to a local path (for example `data/local.yaml`) and set secrets in your environment — never commit credentials.

Verify the install:

```bash
uv run python src/main.py --help
uv run pytest
```

## Configuration

Non-secret settings live in YAML (`--config` or `REPORTING_APP_CONFIG`). Secrets come from environment variables only.

| Variable | Required | Role |
| -------- | -------- | ---- |
| `AZURE_DEVOPS_PAT` | For ADO and export | Azure DevOps PAT (HTTP Basic password; empty username) |
| `ELASTICSEARCH_URL` | For export and ES smoke | Cluster endpoint |
| `ELASTICSEARCH_API_KEY` | Preferred for ES | API key auth |
| `ELASTICSEARCH_USERNAME` / `ELASTICSEARCH_PASSWORD` | Alternative to API key | Basic auth |
| `REPORTING_APP_CONFIG` | Optional | Default YAML path when `--config` is omitted |

Full reference: **[CONFIGURATION.md](CONFIGURATION.md)**.

## Usage

### Export (ADO → Elasticsearch)

Run one export from configuration:

```bash
export AZURE_DEVOPS_PAT='***'
export ELASTICSEARCH_URL='https://***'
export ELASTICSEARCH_API_KEY='***'

uv run python src/main.py export \
  --config data/reporting.sample.yaml \
  --project snykDemoProject
```

Optional scope overrides (CLI wins over YAML):

| Flag | Purpose |
| ---- | ------- |
| `--org` | Restrict to one ADO organization |
| `--project` | Restrict to one ADO project |
| `--filter-tag` | Override WIQL tag filter |

Stdout is **NDJSON audit logs**, not work item JSONL. Grep the run summary:

```bash
uv run python src/main.py export \
  --config data/reporting.sample.yaml \
  --project snykDemoProject | \
  grep export_summary
```

Example summary fields: `work_items_discovered`, `documents_written`, `documents_failed`, `export_outcome` (`success`, `partial`, or `failure`).

Exit code `0` on `success`; `1` on partial/failure or configuration/auth errors.

### Azure DevOps smoke

Verify read-only ADO access and print normalized work items as JSON lines:

```bash
export AZURE_DEVOPS_PAT='***'

uv run python src/main.py azure-devops-smoke wiql \
  --config data/reporting.sample.yaml \
  --project snykDemoProject
```

### Elasticsearch smoke

Index one reporting document to verify cluster access:

```bash
export ELASTICSEARCH_URL='https://***'
export ELASTICSEARCH_API_KEY='***'

uv run python src/main.py elasticsearch-smoke index-one \
  --config data/reporting.sample.yaml
```

## Kibana setup

After a successful export populates the index (default `snyk-ado-work-items`):

### 1. Create a data view

1. Open **Stack Management → Data Views → Create data view**
2. Name: `Snyk ADO work items` (or your preference)
3. Index pattern: `snyk-ado-work-items` (or your configured `elasticsearch.index_name`)
4. Timestamp field: **`work_item.created_at`**
5. Save

### 2. Create a Discover saved search

Use **Discover** (not Lens) for a full, searchable list of work items. Lens tables aggregate data and are a poor fit for browsing every document.

1. Open **Analytics → Discover**
2. Data view: the data view from step 1
3. Time range: set wide enough to include your work items (for example **Last 1 year**). Discover filters on **`work_item.created_at`** (when the item was created in Azure DevOps), not **`export.exported_at`** (when the export last synced the document).
4. Click **Columns** (+) and add:

| Column | Field |
| ------ | ----- |
| Work item ID | `work_item.id` |
| Title | `work_item.title` |
| Assignee | `work_item.assignee` |
| Project | `work_item.project` |
| Status | `work_item.status` |
| Severity | `tags.severity` |
| Finding type | `tags.finding_type` |
| Story | `work_item.story_name` |
| Story link | `work_item.story_url` |
| Work item link | `work_item.url` |
| Created | `work_item.created_at` |
| Closed | `work_item.closed_at` |
| Days to close | `work_item.days_to_close` |

5. Sort by **`work_item.created_at`** descending (click the column header)
6. **Save** the search (for example `Snyk ADO work items`)

To add the table to a dashboard: **Analytics → Dashboard → Create dashboard → Add panel → Saved search**, then select the saved search from step 6.

### 3. Optional filters

Add Discover sidebar filters or KQL queries for:

- `work_item.organization`
- `work_item.project`
- `tags.severity`
- `tags.finding_type`
- `work_item.status`
- `tags.operator`

Some documents may have null `tags.severity` or `tags.finding_type` when managed tags are absent — that is expected.

## Testing

```bash
uv run pytest
```

See **[CONTRIBUTING.md § Test layout](CONTRIBUTING.md#test-layout)**.

## Troubleshooting

- **Missing `AZURE_DEVOPS_PAT` or `ELASTICSEARCH_URL`**: set env vars before running export; errors go to stderr without credential material.
- **Configuration file not found**: pass `--config` or set `REPORTING_APP_CONFIG`.
- **Partial export (`export_outcome=partial`)**: check stderr and `errors` in the export summary NDJSON line; exit code is `1`.
- **Empty or sparse Discover results**: widen the time range — the data view time field is `work_item.created_at` (ADO creation time), not `export.exported_at`. Also confirm export wrote documents (`documents_written` > 0) and the data view index pattern matches your config.

More detail: **[CONFIGURATION.md](CONFIGURATION.md)**.

## Deployment

Build and run from the root `Dockerfile` for scheduled export jobs. Mount configuration at `/config/reporting.yaml` or set `REPORTING_APP_CONFIG`. Inject secrets via your platform's secret store.

Container and CI notes: **[CONTRIBUTING.md § CI, releases, and containers](CONTRIBUTING.md#ci-releases-and-containers)**.

## More documentation

| Document | Audience |
| -------- | -------- |
| **[CONFIGURATION.md](CONFIGURATION.md)** | Full configuration reference: files, env vars, CLI flags, commands |
| **[CONTRIBUTING.md](CONTRIBUTING.md)** | Layout, OpenSpec, tests, CI/Docker |
