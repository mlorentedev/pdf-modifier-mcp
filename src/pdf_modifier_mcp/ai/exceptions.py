"""AI exceptions for NaN Cloud operations."""

from __future__ import annotations

from ..core.exceptions import PDFModifierError


class AIError(PDFModifierError):
    """Base exception for AI operations."""

    code = "AI_ERROR"


class AIAuthenticationError(AIError):
    """Raised when API authentication fails."""

    code = "AI_AUTH_ERROR"


class AIRateLimitError(AIError):
    """Raised when rate limit is exceeded."""

    code = "AI_RATE_LIMIT"


class AIServerError(AIError):
    """Raised when AI server returns an error."""

    code = "AI_SERVER_ERROR"
