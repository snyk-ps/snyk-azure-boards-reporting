# Snyk Azure Boards Reporting

Export Snyk-tagged Azure DevOps work items to Elasticsearch for Kibana reporting. The application reads work items via WIQL, normalizes them into reporting documents, and bulk-upserts them into a configured Elasticsearch index. Azure DevOps access is read-only.

Typical deployment is a **scheduled container** (for example **Azure Container Apps**) running **`export`** on a **every 2 hours** cadence; the same build is also easy to run on a workstation for smoke tests and debugging.

## Table of contents

- [Quick start](#quick-start)
- [Installation and setup](#installation-and-setup)
  - [Development / local installation](#development-local-installation)
  - [Deployment / production installation](#deployment-production-installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Kibana setup](#kibana-setup)
- [Testing](#testing)
- [Deployment](#deployment)
  - [Azure Container Apps: portal walkthrough (scheduled job)](#azure-container-apps-portal-walkthrough-scheduled-job)
- [Logs and observability](#logs-and-observability)
- [Troubleshooting](#troubleshooting)
- [More documentation](#more-documentation)

## Quick start

Pick an installation path below. Both use the same **secrets** and **YAML policy** model.

**Development / local**

1. Clone the repo, **`uv sync --dev`**, set **`AZURE_DEVOPS_PAT`**, **`ELASTICSEARCH_URL`**, and **`ELASTICSEARCH_API_KEY`**, copy **`data/reporting.sample.yaml`** and adjust it (see [Development / local installation](#development-local-installation)).
2. Run **`uv run python src/main.py export --config /path/to/your-config.yaml`**.

**Deployment / production**

1. Run the app from a **container** on your platform (commonly a **scheduled** job on **Azure Container Apps**). The image **defaults to** **`export --config /config/reporting.yaml`** (mount your YAML there or override args). Schedule **`export` every 2 hours** (recommended). Inject secrets and mount or supply **`--config`** (see [Deployment / production installation](#deployment-production-installation) and [Deployment](#deployment)).

Full YAML and environment reference: **[CONFIGURATION.md](CONFIGURATION.md)**.

## Installation and setup

### Prerequisites

- **Azure DevOps** personal access token with **read** access to work items
- **Elasticsearch** cluster (Elastic Cloud or self-hosted) with API key or basic auth
- **Development / local:** **Python** 3.12+ and **[uv](https://docs.astral.sh/uv/getting-started/installation/)**
- **Deployment / production:** a container runtime and outbound **HTTPS** to **`dev.azure.com`** and your Elasticsearch endpoint; **Docker** optional for building images locally

### Secrets and environment (both paths)

| Variable | Required for `export` | Role |
| -------- | --------------------- | ---- |
| **`AZURE_DEVOPS_PAT`** | Yes | Azure DevOps PAT (**secret**; HTTP Basic password with empty username). |
| **`ELASTICSEARCH_URL`** | Yes | Cluster endpoint (**secret** in some setups; never log). |
| **`ELASTICSEARCH_API_KEY`** | Yes (or username/password) | API key auth (**secret**). |
| **`REPORTING_APP_CONFIG`** | No | Overrides default YAML path when `--config` is omitted. |

**Never** put tokens or credentials in YAML; use the process environment or your platform's secret store (Key Vault, Container Apps secrets, etc.).

All variables and overrides: **[CONFIGURATION.md § Environment variables](CONFIGURATION.md#environment-variables)**.

### Development / local installation

Use this path to contribute, debug, or smoke-test from your machine.

1. **Clone** and install dependencies:

```bash
uv sync --dev
```

2. **Configure** policy: copy **`data/reporting.sample.yaml`**, set **`azure_devops.organizations`**, and **`elasticsearch`** settings (full reference: **[CONFIGURATION.md](CONFIGURATION.md)**).

3. **Export secrets** in your shell:

```bash
export AZURE_DEVOPS_PAT='***'
export ELASTICSEARCH_URL='https://***'
export ELASTICSEARCH_API_KEY='***'
```

4. **Run** the CLI:

```bash
uv run python src/main.py --help
uv run python src/main.py export --config data/reporting.sample.yaml
```

Optional: build and run the root **`Dockerfile`** locally to mirror production; see **[CONTRIBUTING.md § CI, releases, and containers](CONTRIBUTING.md#ci-releases-and-containers)**.

### Deployment / production installation

Use this path for scheduled export in a cluster or cloud (recommended for ongoing operations).

1. **Image:** use a build from this repo's **`Dockerfile`**, or pull a release image from **[GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)** (**`ghcr.io`**) when published. The image **ENTRYPOINT** is **`python src/main.py`**; **default args** are **`export --config /config/reporting.yaml`** (mount policy there unless your platform overrides **command** / **args**). See **[CONTRIBUTING.md](CONTRIBUTING.md)** for enabling GHCR releases.

2. **Secrets:** inject **`AZURE_DEVOPS_PAT`**, **`ELASTICSEARCH_URL`**, and **`ELASTICSEARCH_API_KEY`** via your platform (for example Key Vault references on **Azure Container Apps**), not in the image or YAML.

3. **Policy:** supply non-secret config as a mounted file at **`/config/reporting.yaml`** (recommended, matches the default **`CMD`**), or set **`REPORTING_APP_CONFIG`** / override **`--config`** per **[CONFIGURATION.md](CONFIGURATION.md)**.

4. **Job model:** run **`export`** on a **schedule** (Container Apps **cron**). **Recommended:** trigger **`export` every 2 hours** so Kibana stays reasonably fresh without excessive API load. If you use the image defaults, the job only needs to **start the container** with secrets and the config mount. Production jobs run the **full scope** defined in mounted YAML (no CLI scope overrides on the job).

**`docker run` example** (replace image tag; use a real config file path on the host):

```bash
docker run --rm \
  -e AZURE_DEVOPS_PAT \
  -e ELASTICSEARCH_URL \
  -e ELASTICSEARCH_API_KEY \
  -v /path/on/host/reporting.yaml:/config/reporting.yaml:ro \
  ghcr.io/snyk-ps/snyk-azure-boards-reporting:<tag>
```

Other CLI subcommands override the default args, for example: **`docker run … <image> azure-devops-smoke wiql --config /config/reporting.yaml`**. Show help with **`docker run … <image> --help`**.

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

Optional scope overrides for **local development and smoke tests** (CLI wins over YAML):

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

## Deployment

This section is the **Azure-oriented runbook** for production: sizing and the **[portal walkthrough](#azure-container-apps-portal-walkthrough-scheduled-job)** for a **scheduled Container App Job**.

Production is commonly a **scheduled container** on **[Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/overview)** using images from **`ghcr.io`** when published. **No Bicep/Terraform** is required in this repo. **Schedule `export` every 2 hours** unless your cadence needs adjustment.

### Minimum requirements (Azure Container Apps)

| Area | Recommendation |
| ---- | -------------- |
| **`export` schedule** | **Every 2 hours** is recommended (for example cron `0 */2 * * *` UTC); export runs are typically short-lived. |
| **CPU / memory** | Start around **0.5 vCPU** and **1 GiB**; increase if runs are slow or OOM. |
| **Replicas** | **1** is usually enough if jobs do not overlap. |
| **Replica timeout** | Set **`replicaTimeout`** (seconds) to at least the longest **`export`** run you expect, plus buffer. Default is **30 minutes** ([job configuration](https://learn.microsoft.com/en-us/azure/container-apps/jobs?tabs=azure-cli#job-execution-configuration)). Tune from **`export_summary`** → **`export_duration_seconds`** in logs (see [Logs and observability](#logs-and-observability)); set timeout above observed peak with margin (e.g. **1.5–2×**). |
| **Networking** | Outbound **HTTPS** to **`dev.azure.com`** and your Elasticsearch endpoint. |
| **Secrets** | **`AZURE_DEVOPS_PAT`**, **`ELASTICSEARCH_URL`**, **`ELASTICSEARCH_API_KEY`** via Key Vault references / Container Apps secrets, not the image. |

### Azure Container Apps: portal walkthrough (scheduled job)

Use a **Container App Job** with a **Schedule** trigger (cron), not a regular HTTP Container App. The steps below follow the [Create a job in the Azure portal](https://learn.microsoft.com/en-us/azure/container-apps/jobs-get-started-portal) flow and this repo's image default **`export --config /config/reporting.yaml`**.

#### A. Prepare config in Azure Storage (do this first)

1. In the portal, open **Storage accounts** → **+ Create**.
2. **Basics:** pick subscription, resource group, region, a **globally unique** name, **Performance** Standard, **Redundancy** LRS (or per policy). **Kind** StorageV2 is fine.
3. **Advanced:** ensure **Allow storage account key access** stays **enabled** if you will use the **account key** for the ACA file share link (common for SMB).
4. Create the account, then open it.
5. Under **Data storage** → **File shares** → **+ File share:** create a share (e.g. `snyk-reporting-config`).
6. Open the share → **Upload** your **`reporting.yaml`** (non-secret policy only).  
   The object in the share must end up as **`reporting.yaml`** at the **root** of the share so the mounted path **`/config/reporting.yaml`** is correct.
7. Under **Security + networking** → **Access keys:** copy **key1** (or **key2**) — you'll paste it when wiring the environment **Volume mount**.

**Networking:** If the storage account uses a **restricted firewall** or **public network access** disabled, SMB mounts from Container Apps can fail (for example **`VolumeMountFailure`** / **`mount error(13): Permission denied`**). The account must be **reachable** from your Container Apps environment for that file share. See [Use storage mounts in Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/storage-mounts).

#### B. Create the Container Apps environment (with file share link)

1. Portal search: **Container Apps environments** → open your environment (or create it from the job wizard via **Create new**).
2. Open the environment → **Settings** → **Volume mounts** (or **Storage** / **Azure Files**, depending on portal wording).
3. **Add** a volume mount:
   - **Protocol:** SMB (default for standard Azure Files).
   - **Name:** a short logical name you will reuse on the job (e.g. `configshare`).
   - **Storage account:** select the account from step **A**.
   - **File share:** select the share that contains **`reporting.yaml`**.
   - **Access key:** paste the key from step **A** (if the UI asks).
   - **Access mode:** **Read only** is enough if the job only reads config.
4. **Save** so the environment now lists this Azure Files mount.

#### C. Create the Container App Job (scheduled)

1. Portal top search: **Container App Jobs** → **Create**.

**Basics**

- Subscription, **Resource group**
- **Container job name:** e.g. `snyk-ado-reporting-export`
- **Region:** same as the environment (and typically the same as the storage account region).
- **Container Apps environment:** select the environment from **B**.

**Job details**

- **Trigger type:** **Scheduled**
- **Cron expression:** use a **five-field** schedule in **UTC**. Recommended: **`0 */2 * * *`** (every 2 hours). Adjust to your cadence.
- **Replica timeout:** set above your longest observed **`export`** run (see **`export_summary`** in [Logs and observability](#logs-and-observability)). Platform default is **30 minutes**.

**Container**

- **Container name:** e.g. `main`
- **Image source:** **Docker Hub or other registries** (or **Azure Container Registry** if you use ACR).
- For **`ghcr.io`:** set **registry** to **`ghcr.io`**, image **`snyk-ps/snyk-azure-boards-reporting:<tag>`** (pin a real **tag** or **digest**). If the package is **private**, set **registry credentials** per portal prompts.
- **Workload profile:** **Consumption** is usually fine for this export.
- **CPU and memory:** e.g. **0.5 CPU**, **1.0 Gi**.

**Do not** override **ENTRYPOINT** / **command** for normal production; the image default is already **`export --config /config/reporting.yaml`**.

#### D. Secrets and environment variables (portal)

On the job's container configuration. Add **Secrets** (job-level), then reference them from **Environment variables**:

| Secret name | Value |
| ----------- | ----- |
| `azure-devops-pat` | Azure DevOps PAT |
| `elasticsearch-url` | Elasticsearch cluster URL |
| `elasticsearch-api-key` | Elasticsearch API key |

| Variable | Source |
| -------- | ------ |
| `AZURE_DEVOPS_PAT` | Reference secret `azure-devops-pat` |
| `ELASTICSEARCH_URL` | Reference secret `elasticsearch-url` |
| `ELASTICSEARCH_API_KEY` | Reference secret `elasticsearch-api-key` |

**Key Vault:** if your org requires it, use Key Vault references on Container Apps secrets instead of pasting values.

#### E. Mount the file share on the job at `/config`

1. In the **Container** step (or **Volumes** / **Advanced**), **add a volume:**
   - **Type:** **Azure Files** (backed by the environment mount you named, e.g. `configshare`).
2. **Mount** that volume on the main container:
   - **Mount path:** **`/config`**
   - No **`subPath`** needed if **`reporting.yaml`** is at the **root** of the share.

If the **create** wizard does not offer volumes, finish **Create**, then open the job → **Containers** / **Edit**, add the volume and **`/config`** mount, then **save**.

#### F. Deploy, test, logs

1. **Review + create** on the job.
2. Open the job → **Execution history** → **Run now** / manual start to test before waiting for cron.
3. Open **Log stream** or **Logs**; confirm **`export_summary`** / **`integration_audit`** lines (see [Logs and observability](#logs-and-observability)).

**Exit reason:** **`ProcessExited`** with **exit code `0`** means the export finished successfully.

#### G. If something fails

| Issue | What to check |
| ----- | ------------- |
| **Missing config** | The share contains **`reporting.yaml`** and the mount path is exactly **`/config`**. |
| **Volume mount / Permission denied** | Storage account **firewall** / **public network access**, wrong **access key**, or share path; see **A** and [Use storage mounts in Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/storage-mounts). |
| **Auth errors** | Secrets, PAT read scope, Elasticsearch API key and index permissions. |
| **Job stops at ~30 minutes** | Increase **Replica timeout**; tune from **`export_duration_seconds`** in **`export_summary`** logs. |
| **Pull image failed** | **`ghcr.io`** visibility and **registry credentials** on the job. |
| **Elasticsearch unreachable** | Outbound HTTPS from ACA to your cluster endpoint; cluster firewall / IP allowlist (operator responsibility). |

### Container registry

The image **defaults to** **`export --config /config/reporting.yaml`**. When GHCR publishing is enabled (see **[CONTRIBUTING.md](CONTRIBUTING.md)**), images are published to **`ghcr.io/<owner>/<repository>:<tag>`**. Authenticate your runtime to **`ghcr.io`**; pin **tags** or **digests**. [Working with the Container registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).

## Logs and observability

The **`export`** command emits **NDJSON** (one **JSON object per line**) on **standard output**. Each line includes **`timestamp`** (UTC), **`level`**, **`logger`**, and optional fields:

| Field | When present |
|--------|----------------|
| **`record`** | Structured payloads for the **`integration_audit`** logger. |
| **`message`** | Plain messages from other loggers. |
| **`exception`** | Traceback text when a logged exception is attached. |

The **`integration_audit`** **`record`** object uses these **`event`** values:

| `record.event` | Meaning |
|--------|---------|
| **`integration_http`** | One line per terminal Azure DevOps or Elasticsearch HTTP result. Includes `method`, `http_status`, `duration_ms`, `safe_target` (no secrets). |
| **`export_summary`** | One line per **`export`**: **`export_duration_seconds`**, **`work_items_discovered`**, **`documents_written`**, **`documents_failed`**, **`export_outcome`** (`success` / `partial` / `failure`). |

Example line (runtime output is a **single** line):

```text
{"level":"INFO","logger":"integration_audit","record":{"documents_written":42,"event":"export_summary","export_duration_seconds":8.5,"export_outcome":"success","work_items_discovered":42},"timestamp":"2026-07-28T01:15:30.123Z"}
```

For line-oriented shipping in containers, **`PYTHONUNBUFFERED=1`** is set in the Dockerfile.

### Log Analytics (Kusto)

Console logs often land in **`ContainerAppConsoleLogs_CL`**. Parse NDJSON and filter export outcomes, for example:

```kusto
ContainerAppConsoleLogs_CL
| where Log_s startswith "{"
| extend J = parse_json(Log_s)
| where J.logger == "integration_audit"
| extend evt = J.record.event
| where evt == "export_summary" and J.record.export_outcome != "success"
```

Alert on slow exports using **`J.record.export_duration_seconds`** and auth failures on **`integration_http`** with **`http_status`** in **`401`**, **`403`**.

### Where to view logs

- **Log stream:** [Container App log streaming](https://learn.microsoft.com/en-us/azure/container-apps/log-streaming).
- **Log Analytics:** query workspace linked to the ACA environment; structured lines often appear in **`ContainerAppConsoleLogs_CL`**.

## Troubleshooting

- **Missing `AZURE_DEVOPS_PAT` or `ELASTICSEARCH_URL`**: set env vars before running export; errors go to stderr without credential material.
- **Configuration file not found**: pass `--config` or set `REPORTING_APP_CONFIG`; in containers mount **`/config/reporting.yaml`**.
- **Partial export (`export_outcome=partial`)**: check stderr and counts in the **`export_summary`** NDJSON line; exit code is `1`.
- **Empty or sparse Discover results**: widen the time range — the data view time field is `work_item.created_at`, not `export.exported_at`. Confirm **`documents_written` > 0** in **`export_summary`**.

| Symptom | What to check |
| ------- | ------------- |
| **ADO HTTP 401 / 403** | **`AZURE_DEVOPS_PAT`** validity and read access to work items in configured orgs/projects. |
| **Elasticsearch auth failure** | **`ELASTICSEARCH_URL`**, **`ELASTICSEARCH_API_KEY`**, index write permissions. |
| **No documents written** | WIQL tag filter, org/project scope in YAML, work items tagged in ADO. |
| **Job timeout** | Increase replica timeout; review **`export_duration_seconds`** in logs. |

More detail: **[CONFIGURATION.md](CONFIGURATION.md)**.

## More documentation

| Document | Audience |
| -------- | -------- |
| **[CONFIGURATION.md](CONFIGURATION.md)** | Full configuration reference: files, env vars, CLI flags, commands |
| **[CONTRIBUTING.md](CONTRIBUTING.md)** | Layout, OpenSpec, tests, CI/Docker |
