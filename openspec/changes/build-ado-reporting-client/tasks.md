## 1. Scaffold

- [x] 1.1 Create `src/integrations/azure_devops_reporting/` package (`auth`, `http`, `client`, `models`)
- [x] 1.2 Create `src/config/loader.py` — load YAML; validate non-empty `azure_devops.organizations[]` (R1-FR-CFG-7 subset)
- [x] 1.3 Add `data/reporting.sample.yaml` per R1-FR-CFG-8 (no secrets)

## 2. Client (R1-FR-ADO-2 through R1-FR-ADO-9)

- [x] 2.1 Implement `auth.py` — read `AZURE_DEVOPS_PAT`, build Basic header, fail fast when missing
- [x] 2.2 Implement `http.py` — stdlib HTTP with `api-version=7.1`, safe errors, bounded 5xx retry
- [x] 2.3 Implement `client.list_projects(organization)` — paginated project list
- [x] 2.4 Implement `client.query_work_item_ids(organization, project, filter_tag)` — WIQL with tag sanitization
- [x] 2.5 Implement `client.get_work_items_batch(organization, project, ids)` — enforce max 200 before HTTP
- [x] 2.6 Implement `models.normalize_work_item(api_item)` → `{ work_item_id, work_item_status, fields }`
- [x] 2.7 Add unit tests for all public/protected client surfaces (mocked HTTP)

## 3. Smoke CLI (R1-FR-ADO-10)

- [x] 3.1 Create `src/commands/azure_devops_smoke.py` — `wiql` action with `--org`, `--project`, `--filter-tag`, `--config`
- [x] 3.2 Wire `azure-devops-smoke` subcommand in `src/main.py`
- [x] 3.3 Emit normalized JSONL to stdout; chunk batch calls at 200 IDs
- [x] 3.4 Add tests for argparse wiring and stdout JSONL format (mock client)

## 4. Optional local helper

- [x] 4.1 Create `src/commands/output.py` — read JSONL from stdin/file with optional `--pretty` (skip if timeboxed)

## 5. Documentation

- [x] 5.1 Update `CONFIGURATION.md` — `AZURE_DEVOPS_PAT`, sample config path, smoke command, CLI precedence
- [x] 5.2 Add manual smoke example to README Usage section

## 6. Archive prep

- [ ] 6.1 Merge `openspec/specs/` only when archiving: do **not** copy or merge `openspec/changes/build-ado-reporting-client/specs/*.md` into `openspec/specs/` during implementation; run `openspec archive build-ado-reporting-client` when complete
