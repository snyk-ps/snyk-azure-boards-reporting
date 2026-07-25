## ADDED Requirements

### Requirement: Parent story hydration (R1-FR-EXP-13)

Before building reporting documents, export SHALL:

1. Collect unique non-null **`System.Parent`** values from hydrated work items in the current org/project scope.
2. Batch-hydrate those parent IDs for **`System.Id`** and **`System.Title`** (chunks of at most 200).
3. Supply a parent id → title map to `build_reporting_document()` via transform context.

Failure to hydrate an individual parent SHALL NOT fail export for other work items.

#### Scenario: Shared parent across findings

- **WHEN** three findings share parent id `500`
- **THEN** export SHALL perform one parent batch lookup for `500` and stamp the same `work_item.story_name` on all three documents

#### Scenario: No parents in result set

- **WHEN** no hydrated item has `System.Parent`
- **THEN** export SHALL skip the parent batch pass and emit documents with null story fields
