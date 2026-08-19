## ADDED Requirements

### Requirement: URL-encoded path segments on REST requests (R1-FR-ADO-12)

The client SHALL percent-encode **`organization`** and **`project`** names when they appear as path segments in Azure DevOps REST URLs, using stdlib `urllib.parse.quote` with `safe=""` (empty safe set), consistent with reporting document URL construction.

This SHALL apply to:

- List projects: `GET /{organization}/_apis/projects`
- WIQL: `POST /{organization}/{project}/_apis/wit/wiql`
- Work items batch: `POST /{organization}/{project}/_apis/wit/workitemsbatch`

Callers SHALL pass raw ADO organization and project names (not pre-encoded).

#### Scenario: Organization name with space

- **WHEN** the client lists projects for organization `test org`
- **THEN** the HTTP request path SHALL contain `test%20org` as the organization segment

#### Scenario: Project name with space

- **WHEN** the client runs WIQL for organization `example-org` and project `Project Name`
- **THEN** the HTTP request path SHALL contain `Project%20Name` as the project segment

#### Scenario: URL-safe names unchanged

- **WHEN** organization is `torstencannell` and project is `snykDemoProject`
- **THEN** encoded path segments SHALL equal the original names
