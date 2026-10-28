"""AI Provider factory and registry for multi-provider support."""

import logging
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.services.ai.base import BaseAiProvider
from app.services.ai.claude_provider import ClaudeProvider
from app.services.ai.exceptions import AiConfigurationError
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.openai_provider import OpenAiProvider

logger = logging.getLogger(__name__)

SUPPORTED_PROVIDERS = ("gemini", "claude", "openai")

PROVIDER_NAMES: Dict[str, str] = {
    "gemini": "Google Gemini",
    "claude": "Anthropic Claude",
    "openai": "OpenAI",
}

# Provider singleton instances
_instances: Dict[str, BaseAiProvider] = {}


def get_available_providers() -> List[dict]:
    """Return public metadata on supported providers and models without exposing secrets."""
    settings = get_settings()

    def is_gemini_configured() -> bool:
        k = settings.GEMINI_API_KEY
        return bool(k and k.strip() and "your-gemini" not in k.lower() and k.strip() != '""')

    def is_claude_configured() -> bool:
        k = settings.ANTHROPIC_API_KEY
        return bool(k and k.strip() and "your-anthropic" not in k.lower() and k.strip() != '""')

    def is_openai_configured() -> bool:
        k = settings.OPENAI_API_KEY
        return bool(k and k.strip() and "your-openai" not in k.lower() and k.strip() != '""')

    return [
        {
            "id": "gemini",
            "name": PROVIDER_NAMES["gemini"],
            "model": settings.GEMINI_MODEL,
            "configured": is_gemini_configured(),
        },
        {
            "id": "claude",
            "name": PROVIDER_NAMES["claude"],
            "model": settings.ANTHROPIC_MODEL,
            "configured": is_claude_configured(),
        },
        {
            "id": "openai",
            "name": PROVIDER_NAMES["openai"],
            "model": settings.OPENAI_MODEL,
            "configured": is_openai_configured(),
        },
    ]


def get_ai_provider(provider: Optional[str] = None) -> BaseAiProvider:
    """Retrieve or instantiate an AI provider adapter.

    Validates against allowlist ('gemini', 'claude', 'openai').
    Defaults to settings.AI_DEFAULT_PROVIDER if omitted.
    Strictly avoids silent fallbacks.
    """
    settings = get_settings()
    provider_key = (provider or settings.AI_DEFAULT_PROVIDER or "gemini").lower().strip()

    if provider_key not in SUPPORTED_PROVIDERS:
        supported_str = ", ".join(SUPPORTED_PROVIDERS)
        raise AiConfigurationError(
            f"Unsupported AI provider '{provider_key}'. Supported providers: {supported_str}."
        )

    if provider_key not in _instances:
        if provider_key == "gemini":
            _instances["gemini"] = GeminiProvider()
        elif provider_key == "claude":
            _instances["claude"] = ClaudeProvider()
        elif provider_key == "openai":
            _instances["openai"] = OpenAiProvider()

    return _instances[provider_key]
