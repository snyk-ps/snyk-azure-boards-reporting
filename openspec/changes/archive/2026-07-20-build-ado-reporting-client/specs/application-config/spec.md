## ADDED Requirements

### Requirement: Sample configuration under data/ (R1-FR-CFG-8)

The repository SHALL ship a committed sample YAML at **`data/reporting.sample.yaml`** demonstrating `azure_devops.organizations[].filter_tag` and at least one example organization/project pair suitable for local smoke tests.

The sample SHALL NOT contain secrets or placeholder PAT values.

#### Scenario: Sample supplies filter tag

- **WHEN** smoke runs with `--config data/reporting.sample.yaml` and no `--filter-tag`
- **THEN** WIQL SHALL use the `filter_tag` from the sample file
