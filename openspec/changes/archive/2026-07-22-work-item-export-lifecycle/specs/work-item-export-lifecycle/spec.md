## ADDED Requirements

### Requirement: CLI scope overrides (R1-FR-EXP-10)

The **`export`** subcommand SHALL accept optional CLI flags:

| Flag | Role |
|------|------|
| `--org` | Restrict run to one ADO organization |
| `--project` | Restrict run to one ADO project (requires resolvable org) |
| `--filter-tag` | Override WIQL tag filter for the run |

Precedence SHALL match `application-config` and smoke commands: CLI overrides YAML org `filter_tag`; built-in default `Snyk` when neither supplies a tag.

When **`--org`** and/or **`--project`** are omitted, export SHALL process full configured scope per R1-FR-EXP-2.

#### Scenario: CLI overrides config filter tag

- **WHEN** YAML has `filter_tag: Snyk` and export runs with `--filter-tag CustomTag`
- **THEN** WIQL SHALL use `CustomTag`

#### Scenario: Narrowed dev run

- **WHEN** export runs with `--config data/reporting.sample.yaml --project snykDemoProject`
- **THEN** export SHALL process only org/project resolved from config and CLI, not all projects in the org

---

### Requirement: Configuration path for export (R1-FR-EXP-11)

Export SHALL load YAML per R1-FR-CFG-1 before resolving scope. Export SHALL fail fast when no configuration path is available.

#### Scenario: Explicit config file

- **WHEN** `export --config data/reporting.sample.yaml` runs
- **THEN** `closed_states`, org scope, and `elasticsearch.index_name` SHALL come from that file

---

### Requirement: Export orchestration module (R1-FR-EXP-12)

The application SHALL implement export orchestration that composes existing integrations without duplicating ADO or ES HTTP logic:

1. Resolve scope
2. ADO WIQL + batch hydrate (R1-FR-EXP-3)
3. `build_reporting_document()` per item (R1-FR-EXP-4, R1-FR-EXP-5)
4. Elasticsearch bulk upsert (R1-FR-EXP-7)

#### Scenario: End-to-end single project

- **WHEN** export runs for one project with matching work items and valid ES credentials
- **THEN** Elasticsearch SHALL contain upserted reporting documents and stdout SHALL include `export_summary` with matching discovered and written counts
