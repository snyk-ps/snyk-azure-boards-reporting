"""Domain errors for the Azure DevOps reporting client."""


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""


class MissingPatError(ConfigurationError):
    """Raised when AZURE_DEVOPS_PAT is unset or empty."""


class AuthenticationError(Exception):
    """Raised when Azure DevOps rejects credentials."""


class InvalidFilterTagError(ValueError):
    """Raised when a WIQL filter tag contains invalid characters."""


class BatchLimitError(ValueError):
    """Raised when a batch request exceeds the allowed ID count."""


class AzureDevOpsHttpError(Exception):
    """Raised when Azure DevOps returns a non-retryable HTTP error."""

    def __init__(self, message: str, *, status: int, safe_target: str) -> None:
        super().__init__(message)
        self.status = status
        self.safe_target = safe_target
