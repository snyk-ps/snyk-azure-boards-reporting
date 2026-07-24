## 1. Azure DevOps client

- [x] 1.1 Add `System.AssignedTo` and `System.Parent` to batch field constants in `src/integrations/azure_devops_reporting/models.py`
- [x] 1.2 Unit tests for normalized records with/without assignee and parent

## 2. Reporting transform

- [x] 2.1 Add `src/reporting/urls.py` with `build_ado_work_item_url(org, project, work_item_id)`
- [x] 2.2 Extend `TransformContext` with optional `parent_titles: dict[int, str]`
- [x] 2.3 Populate `work_item.assignee`, `work_item.url`, `work_item.story_name`, `work_item.story_url` in `build_reporting_document()`
- [x] 2.4 Unit tests: assigned + parent, unassigned + no parent, parent id without title map
- [x] 2.5 Update golden document fixtures if present

## 3. Export orchestration

- [x] 3.1 In `src/export/runner.py`, collect parent IDs and second-pass batch hydrate titles
- [x] 3.2 Pass parent map into transform context per item
- [x] 3.3 Export runner tests with injectable ADO client (shared parent, missing parent)

## 4. Elasticsearch mappings

- [x] 4.1 Add `assignee`, `url`, `story_name`, `story_url` to `data/elasticsearch/snyk-ado-work-items-mappings.json`
- [x] 4.2 Mapping load test still passes

## 5. Documentation

- [x] 5.1 README: extend Discover column table with assignee, story, and link fields
- [x] 5.2 CONFIGURATION.md: brief note that story fields derive from `System.Parent`

## 6. Verification

- [x] 6.1 `uv run pytest`
- [ ] 6.2 Manual smoke: export sample project; confirm new fields in ES and Discover

## 7. Archive (human)

- [ ] 7.1 Merge **`openspec/specs/`** only when archiving: do **not** copy or merge
      **`openspec/changes/work-item-assignee-story-links/specs/*.md`** into **`openspec/specs/`**
      during implementation; run **`openspec archive work-item-assignee-story-links`**
      (or project equivalent) to fold deltas into canonical specs.
