# Elasticsearch platform

## Purpose

Define how export documents are indexed in Elasticsearch: connection, index naming, mappings, bulk ingest, and idempotent upserts.

## Requirements

### Requirement: Secrets via environment (R1-FR-ES-1)

Elasticsearch connection credentials SHALL come from environment variables only:

| Variable | Role |
|----------|------|
| `ELASTICSEARCH_URL` | Cluster endpoint (required) |
| `ELASTICSEARCH_API_KEY` | API key auth (preferred) |
| `ELASTICSEARCH_USERNAME` / `ELASTICSEARCH_PASSWORD` | Basic auth alternative when API key is not used |

The application SHALL NOT read Elasticsearch secrets from YAML or CLI flags. The application SHALL NOT log credentials.

#### Scenario: Missing cluster URL

- **WHEN** `ELASTICSEARCH_URL` is unset
- **THEN** export SHALL fail before bulk ingest with a clear error

---

### Requirement: Index name configuration (R1-FR-ES-2)

Application configuration SHALL specify **`elasticsearch.index_name`** (default **`snyk-ado-work-items`**). Export SHALL write to that index unless a test-only override is documented.

#### Scenario: Default index

- **WHEN** configuration omits `index_name`
- **THEN** documents SHALL be written to index `snyk-ado-work-items`

---

### Requirement: Document id strategy (R1-FR-ES-3)

Bulk upsert SHALL use Elasticsearch **`_id`**:

```
{organization}:{project}:{work_item.id}
```

Example: `torstencannell:snykDemoProject:12345`

This guarantees idempotent re-export per work item within an organization/project scope.

#### Scenario: Upsert same work item twice

- **WHEN** the same work item is exported in two runs
- **THEN** Elasticsearch SHALL contain one document with `_id` matching the stable key and updated fields from the latest run

---

### Requirement: Index mappings (R1-FR-ES-4)

Index template or create-index logic SHALL map fields per `reporting-document-model`:

- All `*.at` and date fields → **`date`**
- Identifiers, status, severity, finding type, enums → **`keyword`**
- `work_item.title` → **`text`** with a **`keyword`** multi-field (`.keyword`) for aggregations

Implementation MAY ship a JSON index template artifact checked into the repository.

#### Scenario: Date field aggregation in Kibana

- **WHEN** Kibana aggregates on `work_item.created_at`
- **THEN** the field SHALL be mapped as `date` not `text`

---

### Requirement: Bulk ingest (R1-FR-ES-5)

Export SHALL send documents using the Elasticsearch **_bulk** API with **`index`** or **`update`** actions and **`doc_as_upsert: true`** (or equivalent index-with-id semantics).

The ingest client SHALL:

- Batch bulk lines (implementation-defined chunk size, documented in design).
- Report partial bulk failures without silently dropping successful lines.
- Fail the export run when bulk failure rate exceeds a documented threshold (default: any unrecoverable auth or index-not-found error fails the run).

Prefer **stdlib HTTP** (`urllib`) for bulk requests when feasible per project guidelines.

#### Scenario: Partial bulk item failure

- **WHEN** one document in a bulk batch fails validation but others succeed
- **THEN** export summary SHALL report success and failure counts separately

---

### Requirement: Index existence (R1-FR-ES-6)

On first export (or via a documented **`index-setup`** subcommand), the application MAY create the index with mappings if it does not exist. Auto-create with dynamic mapping alone is **not** sufficient for production — explicit mappings per R1-FR-ES-4 are required.

#### Scenario: Missing index on first run

- **WHEN** the target index does not exist and auto-setup is enabled
- **THEN** export SHALL create the index with normative mappings before bulk ingest

---

### Requirement: Non-goals (R1-FR-ES-7)

This capability does NOT require:

- Elasticsearch ingest pipelines (v1).
- Index lifecycle management (ILM) policies in-repo.
- Cross-cluster search or CCR.

Operators MAY configure ILM and retention outside this repository.

---

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

The application SHALL provide an **`elasticsearch-smoke index-one`** CLI subcommand that indexes one reporting document into the configured Elasticsearch index without requiring Azure DevOps access.

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
