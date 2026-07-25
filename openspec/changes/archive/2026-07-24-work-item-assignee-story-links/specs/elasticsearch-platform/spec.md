## MODIFIED Requirements

### Requirement: Index mappings artifact and setup (R1-FR-ES-9)

The repository SHALL include a checked-in JSON artifact defining index mappings per R1-FR-ES-4 for the default index name.

The artifact SHALL include explicit **`keyword`** mappings for:

- `work_item.assignee`
- `work_item.url`
- `work_item.story_name`
- `work_item.story_url`

When `elasticsearch.auto_create_index` is `true`, the ingest client SHALL create the target index with those mappings if it does not exist before bulk ingest.

Operators MAY alternatively create the index manually using a documented Dev Tools snippet equivalent to the checked-in mappings.

#### Scenario: Auto-create on first ingest

- **WHEN** the target index does not exist and `auto_create_index` is `true`
- **THEN** ingest SHALL create the index with normative mappings before sending bulk lines

#### Scenario: Manual index setup

- **WHEN** an operator runs the documented Dev Tools snippet against `snyk-ado-work-items`
- **THEN** field types for `work_item.created_at` and `tags.severity` SHALL match R1-FR-ES-4

#### Scenario: Mappings artifact includes assignee and link fields

- **WHEN** an operator loads `data/elasticsearch/snyk-ado-work-items-mappings.json`
- **THEN** `work_item.assignee`, `work_item.url`, `work_item.story_name`, and `work_item.story_url` SHALL be mapped as `keyword`
