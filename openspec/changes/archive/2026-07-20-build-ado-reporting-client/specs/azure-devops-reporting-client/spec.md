## ADDED Requirements

### Requirement: Smoke WIQL CLI (R1-FR-ADO-10)

The application SHALL provide an **`azure-devops-smoke`** argparse subcommand with a **`wiql`** action that exercises WIQL discovery and batch hydration for one organization and one project without Elasticsearch or mapping store.

The subcommand SHALL:

1. Require `AZURE_DEVOPS_PAT` from the environment (R1-FR-ADO-2).
2. Accept **`--org`**, **`--project`**, and optional **`--filter-tag`** (CLI overrides config).
3. Accept optional **`--config`** to load `filter_tag` and defaults from YAML (R1-FR-CFG-2); secrets SHALL NOT come from YAML.
4. Run WIQL (R1-FR-ADO-5), chunk IDs into batches of at most 200 (R1-FR-ADO-6), normalize (R1-FR-ADO-7).
5. Write **one JSON object per normalized work item** to **standard output**, each line valid JSON (JSONL).
6. Exit non-zero on configuration, authentication, or terminal HTTP failure; exit zero when WIQL returns no matches.

Audit NDJSON logging (R1-FR-OBS-1) is NOT required for smoke stdout; stderr MAY carry human-readable errors.

#### Scenario: Smoke with CLI overrides

- **WHEN** `azure-devops-smoke wiql --org torstencannell --project snykDemoProject --filter-tag Snyk` runs with valid PAT and matching work items
- **THEN** stdout SHALL contain one JSON line per normalized work item with keys `work_item_id`, `work_item_status`, and `fields`

#### Scenario: Smoke with zero matches

- **WHEN** WIQL returns no work item IDs
- **THEN** the command SHALL exit 0 and emit no stdout lines

#### Scenario: Missing PAT on smoke

- **WHEN** `AZURE_DEVOPS_PAT` is unset
- **THEN** the command SHALL fail before HTTP and SHALL NOT echo secret material
