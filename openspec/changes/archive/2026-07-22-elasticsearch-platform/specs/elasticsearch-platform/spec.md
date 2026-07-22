## ADDED Requirements

### Requirement: Standalone bulk ingest client (R1-FR-ES-8)

The application SHALL expose an Elasticsearch ingest client that bulk-upserts reporting documents independently of export orchestration.

The client SHALL:

- Read connection settings from environment per R1-FR-ES-1
- Target `elasticsearch.index_name` from application configuration per R1-FR-ES-2
- Derive `_id` per R1-FR-ES-3 from each document's `work_item.organization`, `work_item.project`, and `work_item.id`
- Send requests via the `_bulk` API per R1-FR-ES-5

The ingest client SHALL accept injectable HTTP transport for unit tests.

#### Scenario: Upsert one document via client

- **WHEN** `bulk_upsert_documents` is called with one reporting document and a configured index
- **THEN** the client SHALL POST to `/_bulk` with `_id` `{organization}:{project}:{work_item.id}` and upsert semantics

#### Scenario: Missing cluster URL before bulk

- **WHEN** `ELASTICSEARCH_URL` is unset
- **THEN** the client factory SHALL raise a clear configuration error before any HTTP request

---

### Requirement: Index mappings artifact and setup (R1-FR-ES-9)

The repository SHALL include a checked-in JSON artifact defining index mappings per R1-FR-ES-4 for the default index name.

When `elasticsearch.auto_create_index` is `true`, the ingest client SHALL create the target index with those mappings if it does not exist before bulk ingest.

Operators MAY alternatively create the index manually using a documented Dev Tools snippet equivalent to the checked-in mappings.

#### Scenario: Auto-create on first ingest

- **WHEN** the target index does not exist and `auto_create_index` is `true`
- **THEN** ingest SHALL create the index with normative mappings before sending bulk lines

#### Scenario: Manual index setup

- **WHEN** an operator runs the documented Dev Tools snippet against `snyk-ado-work-items`
- **THEN** field types for `work_item.created_at` and `tags.severity` SHALL match R1-FR-ES-4

---

### Requirement: Elasticsearch smoke CLI (R1-FR-ES-10)

The application SHALL provide an **`elasticsearch-smoke index-one`** CLI subcommand that indexes one hardcoded reporting document into the configured Elasticsearch index without requiring Azure DevOps access.

The command SHALL:

- Read Elasticsearch credentials from environment per R1-FR-ES-1
- Read `elasticsearch.index_name` and `elasticsearch.auto_create_index` from application configuration
- Use the ingest client per R1-FR-ES-8
- Print a JSON summary to stdout (`_id`, `index_name`, bulk result counts)
- Exit non-zero on configuration, auth, or bulk failures without logging credentials

#### Scenario: Index one document successfully

- **WHEN** `ELASTICSEARCH_URL` and credentials are valid and bulk upsert succeeds
- **THEN** the command SHALL exit `0` and stdout SHALL include the stable document `_id`

#### Scenario: Missing cluster URL

- **WHEN** `ELASTICSEARCH_URL` is unset
- **THEN** the command SHALL exit non-zero before any HTTP request with a clear error on stderr
