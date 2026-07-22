## ADDED Requirements

### Requirement: Assignee and parent batch fields (R1-FR-ADO-11)

Work items batch hydration (R1-FR-ADO-6) SHALL request these additional fields:

| Field |
|-------|
| `System.AssignedTo` |
| `System.Parent` |

The client SHALL expose batch hydration for a caller-supplied ID list and minimal field set so export can resolve parent titles in a second pass without duplicating HTTP logic.

#### Scenario: Batch includes assignee and parent

- **WHEN** ADO returns a work item with assignee and parent
- **THEN** the normalized `fields` object SHALL include `System.AssignedTo` and `System.Parent`

#### Scenario: Unassigned work item

- **WHEN** ADO omits `System.AssignedTo`
- **THEN** normalization SHALL succeed and represent assignee as absent
