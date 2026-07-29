## ADDED Requirements

### Requirement: Container image config path alignment (R1-FR-CFG-12)

The documented container default path (`/config/reporting.yaml`) SHALL match:

1. `DEFAULT_CONTAINER_CONFIG_PATH` in application code
2. The `--config` argument in the container image default command (R1-FR-DEP-1)

When **`export`** runs without **`--config`** or **`REPORTING_APP_CONFIG`**, the resolved path SHALL be `/config/reporting.yaml`.

#### Scenario: Code and image agree

- **WHEN** `export` runs without `--config` or `REPORTING_APP_CONFIG`
- **THEN** the resolved config path SHALL be `/config/reporting.yaml`

#### Scenario: Dockerfile matches code constant

- **WHEN** the shipped Dockerfile default CMD is inspected
- **THEN** it SHALL include `--config` `/config/reporting.yaml` matching `DEFAULT_CONTAINER_CONFIG_PATH`
