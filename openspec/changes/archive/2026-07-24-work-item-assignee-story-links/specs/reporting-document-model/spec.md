## ADDED Requirements

### Requirement: Assignee and link fields (R1-FR-DOC-8)

The `work_item` object SHALL include:

| Field | ES mapping type | Source |
|-------|-----------------|--------|
| `work_item.assignee` | `keyword` | `System.AssignedTo.displayName`; `null` when unassigned |
| `work_item.url` | `keyword` | ADO work item URL from org, project, and `work_item.id` |
| `work_item.story_name` | `keyword` | Parent work item `System.Title` when `System.Parent` resolves; else `null` |
| `work_item.story_url` | `keyword` | ADO URL for parent id when parent resolves; else `null` |

ADO URLs SHALL use `https://dev.azure.com/{organization}/{project}/_workitems/edit/{id}` with URL-encoded path segments.

#### Scenario: Assigned item with parent story

- **WHEN** a normalized item has `System.AssignedTo.displayName` `Jane Doe`, `System.Parent` `500`, and transform context supplies parent title `Checkout hardening`
- **THEN** the document SHALL set `work_item.assignee` to `Jane Doe`, `work_item.story_name` to `Checkout hardening`, and non-null `work_item.url` and `work_item.story_url`

#### Scenario: Unassigned item without parent

- **WHEN** `System.AssignedTo` is absent and `System.Parent` is absent
- **THEN** `work_item.assignee`, `work_item.story_name`, and `work_item.story_url` SHALL be JSON `null` and `work_item.url` SHALL still be populated

#### Scenario: Parent id present but title lookup missing

- **WHEN** `System.Parent` is `500` but the parent title map has no entry for `500`
- **THEN** `work_item.story_name` and `work_item.story_url` SHALL be `null`
