## ADDED Requirements

### Requirement: Export resolves default config path (R1-FR-CFG-11)

When **`export`** runs without **`--config`**, the application SHALL load configuration from **`REPORTING_APP_CONFIG`** when set, else the documented container default path (for example `/config/reporting.yaml`).

#### Scenario: Env default config

- **WHEN** `REPORTING_APP_CONFIG=data/local.yaml` is set and export runs without `--config`
- **THEN** export SHALL load `data/local.yaml`
