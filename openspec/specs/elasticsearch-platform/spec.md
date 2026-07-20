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
