## ADDED Requirements

### Requirement: Container image default command (R1-FR-DEP-1)

The shipped container image SHALL run as a non-root user with:

- **ENTRYPOINT** `["python", "src/main.py"]`
- **CMD** `["export", "--config", "/config/reporting.yaml"]`

The image SHALL set **`PYTHONUNBUFFERED=1`** for line-oriented log shipping.

Operators MAY override container args for smoke subcommands (`azure-devops-smoke`, `elasticsearch-smoke`) without changing the entrypoint.

#### Scenario: Job starts with image defaults

- **WHEN** a Container App Job starts the image without overriding command or args
- **AND** `/config/reporting.yaml` exists and required secrets are set
- **THEN** one export run SHALL execute and exit with code 0 on success

#### Scenario: Missing config file

- **WHEN** the default command runs and `/config/reporting.yaml` is not a readable file
- **THEN** the process SHALL fail fast with a configuration error and a non-zero exit code

#### Scenario: Smoke subcommand override

- **WHEN** an operator runs `docker run … <image> azure-devops-smoke wiql --config /config/reporting.yaml`
- **THEN** the entrypoint SHALL invoke `python src/main.py` with the overridden args instead of the default export command

---

### Requirement: Configuration mount contract (R1-FR-DEP-2)

Non-secret policy SHALL be supplied at **`/config/reporting.yaml`** (recommended) or via **`REPORTING_APP_CONFIG`** / CLI **`--config`** override per application-config precedence.

The image SHALL NOT embed operator YAML in the image layers.

#### Scenario: Azure Files mount

- **WHEN** an Azure Files share contains `reporting.yaml` at the share root
- **AND** the share is mounted at `/config` on the job container
- **THEN** the default export command SHALL load that file without extra flags

---

### Requirement: Secrets via environment (R1-FR-DEP-3)

Container deployments SHALL inject secrets only via environment variables (or platform secret references mapped to env):

| Variable | Required for export |
|----------|---------------------|
| `AZURE_DEVOPS_PAT` | Yes |
| `ELASTICSEARCH_URL` | Yes |
| `ELASTICSEARCH_API_KEY` (or `ELASTICSEARCH_USERNAME` / `ELASTICSEARCH_PASSWORD`) | Yes |

Secrets SHALL NOT be baked into the image or stored in mounted YAML.

#### Scenario: Missing Elasticsearch credentials

- **WHEN** `export` runs in a container without Elasticsearch credentials
- **THEN** the process SHALL exit non-zero before Elasticsearch HTTP calls

---

### Requirement: Scheduled job model (R1-FR-DEP-4)

Production deployments SHALL use a **scheduled** job trigger (cron), not an HTTP-serving Container App.

The recommended cadence is **every 2 hours** (for example cron `0 */2 * * *` in UTC) because export runs are typically short-lived and operators benefit from fresher reporting data.

Production jobs SHALL run the full scope defined in mounted YAML. CLI scope overrides (`--org`, `--project`, `--filter-tag`) are for local development and smoke testing only and SHALL NOT be documented as production Container App Job configuration in this capability.

#### Scenario: Cron-triggered export

- **WHEN** a scheduled Container App Job fires on cron
- **THEN** exactly one export run SHALL start per execution using the image default command

---

### Requirement: Operator runbook in README (R1-FR-DEP-5)

README SHALL document, at minimum:

1. Dev vs deployment installation paths
2. Minimum Azure Container App Job sizing and **replica timeout** guidance tuned via `export_summary` fields
3. Outbound networking requirements (`dev.azure.com`, Elasticsearch endpoint)
4. Step-by-step Azure portal walkthrough: Storage account + file share → environment volume → scheduled job → secrets → `/config` mount → manual test run
5. Recommended schedule: every 2 hours
6. `docker run` example with env vars and config volume mount
7. Troubleshooting table for common mount, auth, and timeout failures
8. Log Analytics Kusto examples for `export_summary` and `integration_http`

#### Scenario: Operator follows README without IaC

- **WHEN** an operator with Azure Container Apps access follows the README deployment section
- **THEN** they SHALL be able to configure a scheduled export job without repository-supplied Bicep or Terraform

---

### Requirement: Container registry documentation (R1-FR-DEP-6)

README SHALL document pulling release images from **`ghcr.io/<owner>/<repository>:<tag>`** when published, including authentication for private packages and pinning tags or digests.

CONTRIBUTING.md SHALL retain existing guidance for enabling GHCR releases (deleting `.github/template`, adding `VERSION`); this change SHALL NOT require executing that bootstrap.

#### Scenario: Production image reference

- **WHEN** an operator deploys from GHCR
- **THEN** README SHALL point to the container package page and tag or digest pinning guidance
