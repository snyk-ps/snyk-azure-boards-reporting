# OpenSpec agents — snyk-azure-boards-reporting

1. Read **`openspec/config.yaml`** (`context`, then `rules`) for product summary and constraints.
2. Read **`openspec/specs/<capability>/spec.md`** for the capability you are changing; use **R1-FR-*** IDs when citing requirements in this repository.
3. Follow **`.cursor/rules/openspec.mdc`** for propose → review → apply → archive.
4. Follow **`.cursor/rules/guidelines.mdc`** for Python 3.12+, uv, argparse, secrets via environment variables, tests, and Snyk policy.

Capabilities: **`upstream-integration-contract`**, **`azure-devops-reporting-client`**, **`work-item-export-lifecycle`**, **`reporting-document-model`**, **`elasticsearch-platform`**, **`application-config`**, **`observability`**, **`kibana-reporting`**. See **`SPEC.md`** for paths.

Upstream sync repo: [snyk-azure-boards-integration](https://github.com/snyk-ps/snyk-azure-boards-integration). Do not duplicate P2-FR-* sync lifecycle requirements here.
