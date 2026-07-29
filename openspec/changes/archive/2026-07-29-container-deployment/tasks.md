## 1. Container image (R1-FR-DEP-1, R1-FR-CFG-12)

- [x] 1.1 Update `Dockerfile`: `ENTRYPOINT ["python", "src/main.py"]`; `CMD ["export", "--config", "/config/reporting.yaml"]`
- [x] 1.2 Verify `DEFAULT_CONTAINER_CONFIG_PATH` in `src/config/paths.py` matches Dockerfile and docs

## 2. Operator documentation (R1-FR-DEP-2, R1-FR-DEP-5, R1-FR-DEP-6, R1-FR-OBS-7)

- [x] 2.1 Expand README: dev vs deployment quick start, production installation, full Deployment section adapted from `data/context/README.md`
- [x] 2.2 Add ACA portal walkthrough (Storage → env volume → scheduled job → secrets → `/config` mount → test run); recommend every 2 hours (`0 */2 * * *` UTC)
- [x] 2.3 Add minimum requirements table, `docker run` example, logs/Kusto for `export_summary`, troubleshooting table
- [x] 2.4 Extend CONFIGURATION.md: container default path, ACA env-var notes, link to README Deployment; no production scope-override section
- [x] 2.5 Update CONTRIBUTING.md Dockerfile table (ENTRYPOINT/CMD), export `docker run` example; keep existing GHCR/template bootstrap notes unchanged

## 3. Verification

- [ ] 3.1 Local: `docker build` + `docker run` with mounted `data/reporting.sample.yaml` and env vars; confirm `export_summary` on stdout and exit 0
- [ ] 3.2 Confirm `docker run … <image> --help` works via ENTRYPOINT with overridden args
- [x] 3.3 Run `uv run pytest tests/config/test_paths.py` (no code change expected)

## 4. Archive prep

- [x] 4.1 Merge `openspec/specs/` only when archiving: do **not** copy or merge `openspec/changes/container-deployment/specs/*.md` into `openspec/specs/` during implementation; run `openspec archive container-deployment` when complete
