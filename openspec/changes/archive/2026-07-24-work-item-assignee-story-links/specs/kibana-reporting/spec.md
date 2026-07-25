## MODIFIED Requirements

### Requirement: Work item detail table (R1-FR-KIB-2)

A primary table visualization SHALL display:

| Column | Field |
|--------|-------|
| Work item ID | `work_item.id` |
| Title | `work_item.title` |
| Assignee | `work_item.assignee` |
| Project | `work_item.project` |
| Status | `work_item.status` |
| Severity | `tags.severity` |
| Finding type | `tags.finding_type` |
| Story | `work_item.story_name` |
| Story link | `work_item.story_url` |
| Work item link | `work_item.url` |
| Created | `work_item.created_at` |
| Closed | `work_item.closed_at` |
| Days to close | `work_item.days_to_close` |

Rows SHALL be sortable by creation date and closure date.

#### Scenario: Sort by creation date

- **WHEN** the operator sorts the table by created descending
- **THEN** newest work items appear first

#### Scenario: Operator opens work item from Discover

- **WHEN** the operator views the work item link column
- **THEN** the value SHALL be a clickable ADO URL for the finding work item
