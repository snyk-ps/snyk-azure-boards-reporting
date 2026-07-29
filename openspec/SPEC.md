# Snyk Azure Boards reporting — spec index

Draft capability specifications for **[snyk-azure-boards-reporting](https://github.com/snyk-ps/snyk-azure-boards-reporting)** (companion to [snyk-azure-boards-integration](https://github.com/snyk-ps/snyk-azure-boards-integration)).

Copy these into `openspec/specs/` when bootstrapping the reporting repository. Normative project context for AI and tooling belongs in `openspec/config.yaml` (see `config.yaml` in this folder).

| Capability | Path |
|------------|------|
| Upstream integration contract (tag vocabulary, mapping store) | [`specs/upstream-integration-contract/spec.md`](specs/upstream-integration-contract/spec.md) |
| Azure DevOps reporting client (read-only WIT) | [`specs/azure-devops-reporting-client/spec.md`](specs/azure-devops-reporting-client/spec.md) |
| Work item export lifecycle | [`specs/work-item-export-lifecycle/spec.md`](specs/work-item-export-lifecycle/spec.md) |
| Reporting document model (Elasticsearch records) | [`specs/reporting-document-model/spec.md`](specs/reporting-document-model/spec.md) |
| Elasticsearch platform | [`specs/elasticsearch-platform/spec.md`](specs/elasticsearch-platform/spec.md) |
| Application configuration | [`specs/application-config/spec.md`](specs/application-config/spec.md) |
| Observability | [`specs/observability/spec.md`](specs/observability/spec.md) |
| Container deployment (scheduled export jobs) | [`specs/container-deployment/spec.md`](specs/container-deployment/spec.md) |
| Kibana reporting (v2) | [`specs/kibana-reporting/spec.md`](specs/kibana-reporting/spec.md) |

Functional requirements in this repository use **`R1-FR-*`** IDs. Upstream sync requirements remain **`P2-FR-*`** in [snyk-azure-boards-integration](https://github.com/snyk-ps/snyk-azure-boards-integration) and are cited as external dependencies only.
