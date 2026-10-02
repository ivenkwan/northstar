"""Typed, sanitized orchestrator errors (§17.8 envelope sources).

Credential failures are fail-closed (ADR-023): messages never carry key
material, Vault tokens, or resolvable secret paths — only static, code-bearing
text (mirrors the ByokError(ApiErrorCode.AI_CREDENTIAL_UNAVAILABLE) pattern in
services/byok/byok/service.py). Configuration failures surface at startup so a
misconfigured deployment fails loudly (NFR-5).
"""

from __future__ import annotations

from enum import Enum


class OrchestratorErrorCode(str, Enum):
    AI_CREDENTIAL_UNAVAILABLE = "AI_CREDENTIAL_UNAVAILABLE"
    AI_PROVIDER_UNAVAILABLE = "AI_PROVIDER_UNAVAILABLE"
    CONFIG_INVALID = "CONFIG_INVALID"


class OrchestratorError(Exception):
    """Base typed error — mapped by the BFF into the {code, message, correlationId, retryable} envelope."""

    code: OrchestratorErrorCode
    message: str
    status: int
    retryable: bool

    def __init__(self, message: str, *, code: OrchestratorErrorCode, status: int, retryable: bool) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status
        self.retryable = retryable


class AICredentialUnavailableError(OrchestratorError):
    """Call-time credential failure — sanitized, fail-closed, no platform fallback (ADR-023)."""

    def __init__(self, message: str = "AI credential unavailable for provider deepseek") -> None:
        super().__init__(message, code=OrchestratorErrorCode.AI_CREDENTIAL_UNAVAILABLE,
                         status=503, retryable=False)


class ProviderUnavailableError(OrchestratorError):
    """Provider transport failed after bounded retries. Message carries HTTP status codes only."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code=OrchestratorErrorCode.AI_PROVIDER_UNAVAILABLE,
                         status=503, retryable=True)


class ConfigError(OrchestratorError):
    """Invalid deployment configuration — raised at composition time (startup), fail-closed (NFR-5)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code=OrchestratorErrorCode.CONFIG_INVALID,
                         status=500, retryable=False)
