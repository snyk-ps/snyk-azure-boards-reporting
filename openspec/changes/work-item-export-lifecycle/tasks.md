## 1. Export orchestration (R1-FR-EXP-3, R1-FR-EXP-7, R1-FR-EXP-8, R1-FR-EXP-12)

- [ ] 1.1 Add `src/export/runner.py`: scope resolution, WIQL → chunk(200) → batch → transform → bulk
- [ ] 1.2 Generate `export_run_id` (UUID) and `TransformContext` per run/org
- [ ] 1.3 Call `ensure_index` when `auto_create_index: true` before first bulk
- [ ] 1.4 Unit tests with fake ADO + ES transports: happy path, empty WIQL, partial transform failure, partial bulk failure

## 2. Scope and config (R1-FR-EXP-2, R1-FR-EXP-10, R1-FR-EXP-11, R1-FR-CFG-11)

- [ ] 2.1 Implement `resolve_export_scope(config, cli)` — full multi-org/project vs CLI-narrowed
- [ ] 2.2 Implement `resolve_config_path(args)` — `--config` → `REPORTING_APP_CONFIG` → default path
- [ ] 2.3 Unit tests: CLI `--filter-tag` override; `--project` narrow; all-projects when `projects: []`; missing config fails fast

## 3. Export CLI (R1-FR-EXP-1)

- [ ] 3.1 Add `src/commands/export.py` with `export` subcommand: `--config`, `--org`, `--project`, `--filter-tag`
- [ ] 3.2 Wire in `src/main.py`; exit codes per design (0 success, 1 partial/failure)
- [ ] 3.3 Unit tests in `tests/commands/test_export.py` (missing PAT, missing ES URL, success with fakes)

## 4. Observability (R1-FR-OBS-2, R1-FR-OBS-3, R1-FR-OBS-6)

- [ ] 4.1 Emit `integration_http` NDJSON for ADO and ES terminal requests (reuse or add thin audit helper)
- [ ] 4.2 Emit single `export_summary` NDJSON line with `work_items_discovered`, `documents_written`, `documents_failed`, `export_outcome`
- [ ] 4.3 Unit test: summary fields and outcome values (`success`, `partial`, `failure`)

## 5. Documentation

- [ ] 5.1 **README.md**: replace scaffold — product description, env vars (`AZURE_DEVOPS_PAT`, `ELASTICSEARCH_*`), `export` examples with `--config`, Kibana data view + Lens table steps (R1-FR-KIB-9)
- [ ] 5.2 **CONFIGURATION.md**: `export` flags, precedence, env vars, link to README Kibana section
- [ ] 5.3 **CONTRIBUTING.md**: note `src/export/` and `tests/export/` in project layout (minimal)

## 6. Archive prep

- [ ] 6.1 Merge `openspec/specs/` only when archiving: do **not** copy or merge `openspec/changes/work-item-export-lifecycle/specs/*.md` into `openspec/specs/` during implementation; run `openspec archive work-item-export-lifecycle` when complete
