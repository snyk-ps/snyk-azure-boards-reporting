# Application configuration

## Purpose

Define operator YAML for the reporting export application: Azure DevOps scope, WIQL filter tag, closed-state detection, optional mapping store, and Elasticsearch index settings. **Secrets stay in environment variables only.**

## Requirements

### Requirement: Configuration file and precedence (R1-FR-CFG-1)

The application SHALL load non-secret policy from a YAML file. Precedence:

1. CLI **`--config`** path when provided.
2. Environment **`REPORTING_APP_CONFIG`** when set.
3. Documented default path for container deployments (for example `/config/reporting.yaml`).

Secrets (`AZURE_DEVOPS_PAT`, `ELASTICSEARCH_*`, mapping store connection strings) SHALL NOT appear in YAML.

#### Scenario: CLI config overrides env

- **WHEN** `--config data/local.yaml` is passed and `REPORTING_APP_CONFIG` is also set
- **THEN** the CLI path SHALL win

---

### Requirement: azure_devops section (R1-FR-CFG-2)

```yaml
azure_devops:
  organizations:
    - name: "<ado-org-name>"
      filter_tag: Snyk          # optional; default Snyk
      projects: []              # empty = all projects; or explicit list
```

| Key | Type | Default | Role |
|-----|------|---------|------|
| `organizations[].name` | string | required | ADO organization |
| `organizations[].filter_tag` | string | `Snyk` | WIQL `[System.Tags] CONTAINS` value |
| `organizations[].projects` | string[] | `[]` | Project allowlist; empty = enumerate all |

#### Scenario: Default filter tag

- **WHEN** `filter_tag` is omitted for an organization
- **THEN** WIQL SHALL use `Snyk`

#### Scenario: Explicit project list

- **WHEN** `projects: [projA, projB]`
- **THEN** export SHALL query only those two projects

---

### Requirement: reporting section (R1-FR-CFG-3)

```yaml
reporting:
  closed_states:
    - Done
  upstream_contract_version: 1
```

| Key | Type | Default | Role |
|-----|------|---------|------|
| `closed_states` | string[] | `[Closed, Done]` | States treated as closed for closure-date fallback |
| `upstream_contract_version` | integer | `1` | Tag parser contract version |

Operators MUST align **`closed_states`** with upstream sync `work_item_state_closed` values in [snyk-azure-boards-integration](https://github.com/snyk-ps/snyk-azure-boards-integration) configuration.

#### Scenario: Custom closed state

- **WHEN** upstream uses `work_item_state_closed: Done` and `closed_states` includes `Done`
- **THEN** export closure fallback logic SHALL treat `Done` as closed

---

### Requirement: elasticsearch section (R1-FR-CFG-4)

```yaml
elasticsearch:
  index_name: snyk-ado-work-items
  auto_create_index: true
```

| Key | Type | Default | Role |
|-----|------|---------|------|
| `index_name` | string | `snyk-ado-work-items` | Target index |
| `auto_create_index` | boolean | `true` | Create index with mappings if missing |

Cluster URL and credentials come from environment only (`elasticsearch-platform` R1-FR-ES-1).

---

### Requirement: Optional mapping_store section (R1-FR-CFG-5)

```yaml
mapping_store:
  backend: azure_table   # or sqlite
  # sqlite_path: data/mapping_store.sqlite   # when backend sqlite
  # azure_table_name: issuesSyncMappingTable # when backend azure_table
```

Connection endpoints and credentials for Azure Table Storage SHALL come from environment variables (aligned with upstream sync repo naming where practical: `mapping_store_azure_table_endpoint`, etc.).

When **`mapping_store`** is absent, export SHALL proceed without Snyk enrich fields.

#### Scenario: Mapping store disabled

- **WHEN** YAML omits `mapping_store`
- **THEN** export documents SHALL omit the `snyk` object

---

### Requirement: Example configuration (R1-FR-CFG-6)

```yaml
azure_devops:
  organizations:
    - name: torstencannell
      filter_tag: Snyk
      projects: []

reporting:
  closed_states:
    - Done
  upstream_contract_version: 1

elasticsearch:
  index_name: snyk-ado-work-items
  auto_create_index: true

mapping_store:
  backend: azure_table
```

#### Scenario: Minimal valid config

- **WHEN** YAML contains one organization and elasticsearch index name
- **THEN** export SHALL start without requiring mapping_store

---

### Requirement: Validation (R1-FR-CFG-7)

Configuration loading SHALL fail fast with clear errors when:

- `azure_devops.organizations` is empty.
- An organization `name` is blank.
- `upstream_contract_version` is unsupported by the application.

#### Scenario: Empty organizations

- **WHEN** `organizations: []`
- **THEN** configuration loading SHALL fail before export

---

### Requirement: Sample configuration under data/ (R1-FR-CFG-8)

The repository SHALL ship a committed sample YAML at **`data/reporting.sample.yaml`** demonstrating `azure_devops.organizations[].filter_tag` and at least one example organization/project pair suitable for local smoke tests.

The sample SHALL NOT contain secrets or placeholder PAT values.

#### Scenario: Sample supplies filter tag

- **WHEN** smoke runs with `--config data/reporting.sample.yaml` and no `--filter-tag`
- **THEN** WIQL SHALL use the `filter_tag` from the sample file
