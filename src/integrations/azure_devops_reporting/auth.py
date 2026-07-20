"""PAT authentication helpers for Azure DevOps."""

import base64
import os

from integrations.azure_devops_reporting.errors import MissingPatError

PAT_ENV_VAR = "AZURE_DEVOPS_PAT"


def read_pat_from_environ() -> str:
    """Return the Azure DevOps PAT from the environment or fail fast."""
    pat = os.environ.get(PAT_ENV_VAR, "").strip()
    if not pat:
        raise MissingPatError(
            f"{PAT_ENV_VAR} is unset or empty; set it in the environment before calling Azure DevOps."
        )
    return pat


def build_authorization_header(pat: str) -> str:
    """Build an HTTP Basic Authorization header for Azure DevOps."""
    token = base64.b64encode(f":{pat}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"
