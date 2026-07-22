## ADDED Requirements

### Requirement: Minimum Kibana setup documented in README (R1-FR-KIB-9)

Operator documentation in **`README.md`** SHALL describe manual minimum Kibana setup sufficient to satisfy R1-FR-KIB-2 (work item detail table), including:

1. Creating a **data view** on the configured index with time field `work_item.created_at`
2. Creating a **Lens table** with the columns defined in R1-FR-KIB-2
3. Optional global filters per R1-FR-KIB-1

#### Scenario: Operator follows README after first export

- **WHEN** an operator completes export and follows README Kibana steps
- **THEN** they SHALL be able to view sortable work item rows with severity, status, and closure columns without importing saved-object NDJSON from the repository
