## ADDED Requirements

### Requirement: Load reporting.closed_states (R1-FR-CFG-3 implementation)

`load_config` SHALL parse `reporting.closed_states` when present.

When the `reporting` section or `closed_states` key is omitted, the loader SHALL default to `[Closed, Done]` per R1-FR-CFG-3.

#### Scenario: Sample config closed states

- **WHEN** loading `data/reporting.sample.yaml`
- **THEN** `closed_states` SHALL be `[Done]`

#### Scenario: Default when reporting section absent

- **WHEN** YAML contains only `azure_devops` and omits `reporting`
- **THEN** `closed_states` SHALL default to `[Closed, Done]`
