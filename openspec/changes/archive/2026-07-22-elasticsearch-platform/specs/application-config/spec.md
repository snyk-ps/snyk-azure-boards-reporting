## ADDED Requirements

### Requirement: Load elasticsearch section (R1-FR-CFG-4 implementation)

`load_config` SHALL parse `elasticsearch.index_name` and `elasticsearch.auto_create_index` when present.

When the `elasticsearch` section is omitted, the loader SHALL default to `index_name: snyk-ado-work-items` and `auto_create_index: true` per R1-FR-CFG-4.

#### Scenario: Sample config elasticsearch section

- **WHEN** loading `data/reporting.sample.yaml`
- **THEN** `index_name` SHALL be `snyk-ado-work-items` and `auto_create_index` SHALL be `true`

#### Scenario: Default when elasticsearch section absent

- **WHEN** YAML contains only `azure_devops` and omits `elasticsearch`
- **THEN** `index_name` SHALL default to `snyk-ado-work-items` and `auto_create_index` SHALL default to `true`
