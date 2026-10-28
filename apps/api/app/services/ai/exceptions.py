"""Exceptions for AI assistant services and provider adapters."""


class AiError(Exception):
    """Base exception for all AI assistant errors."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AiConfigurationError(AiError):
    """Raised when the AI assistant is misconfigured or missing credentials."""

    def __init__(self, message: str):
        super().__init__(message, status_code=503)


class AiAuthenticationError(AiError):
    """Raised when the AI provider rejects credentials."""

    def __init__(self, message: str = "Invalid or unauthorized AI API key."):
        super().__init__(message, status_code=502)


class AiQuotaError(AiError):
    """Raised when provider rate limits or quota are exhausted."""

    def __init__(self, message: str = "AI API quota or rate limit exceeded. Please wait a moment."):
        super().__init__(message, status_code=429)


class AiTimeoutError(AiError):
    """Raised when the provider request exceeds configured timeout."""

    def __init__(self, message: str = "Request to AI provider timed out. Please try again."):
        super().__init__(message, status_code=504)


class AiProviderError(AiError):
    """Raised when the provider experiences an internal or network failure."""

    def __init__(self, message: str = "Failed to communicate with AI provider."):
        super().__init__(message, status_code=502)
