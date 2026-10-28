"""Google Gemini AI Provider Adapter using official google-genai SDK."""

import asyncio
import logging
from typing import Optional

from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.core.config import get_settings
from app.services.ai.base import BaseAiProvider
from app.services.ai.exceptions import (
    AiAuthenticationError,
    AiConfigurationError,
    AiProviderError,
    AiQuotaError,
    AiTimeoutError,
)
from app.services.ai.models import AiMode, AiRequest, AiResponse
from app.services.ai.prompts import (
    EXPLAIN_SYSTEM_INSTRUCTION,
    HINT_SYSTEM_INSTRUCTION,
    REVIEW_SYSTEM_INSTRUCTION,
    build_user_prompt,
)

logger = logging.getLogger(__name__)


class GeminiProvider(BaseAiProvider):
    """Adapter for Google Gemini Developer API using the official google-genai SDK."""

    def __init__(self, client: Optional[genai.Client] = None):
        self._client = client

    def _get_client(self) -> genai.Client:
        """Lazily initialize or return the Gemini client."""
        settings = get_settings()

        if not settings.AI_ASSISTANT_ENABLED:
            raise AiConfigurationError(
                "AI Assistant is currently disabled. Set AI_ASSISTANT_ENABLED=true in .env to enable."
            )

        api_key = settings.GEMINI_API_KEY
        if not api_key or not api_key.strip() or "your-gemini-api-key" in api_key.lower():
            raise AiConfigurationError(
                "Gemini API key is not configured. Set GEMINI_API_KEY in your .env file to enable AI assistance."
            )

        if self._client is None:
            self._client = genai.Client(api_key=api_key.strip())

        return self._client

    async def generate_response(
        self, request: AiRequest, mode: AiMode
    ) -> AiResponse:
        """Call Gemini model asynchronously with strict timeouts and error mapping."""
        settings = get_settings()
        client = self._get_client()

        if mode == AiMode.EXPLAIN:
            system_instruction = EXPLAIN_SYSTEM_INSTRUCTION
        elif mode == AiMode.HINT:
            system_instruction = HINT_SYSTEM_INSTRUCTION
        else:
            system_instruction = REVIEW_SYSTEM_INSTRUCTION

        user_prompt = build_user_prompt(request, mode)

        # Enforce conservative temperature (0.2 for hints, 0.3 for reviews, 0.4 for explain)
        if mode == AiMode.HINT:
            temperature = 0.2
        elif mode == AiMode.REVIEW:
            temperature = 0.3
        else:
            temperature = 0.4
        model_name = settings.GEMINI_MODEL
        timeout_seconds = settings.GEMINI_TIMEOUT_SECONDS

        logger.info(
            "Calling Gemini model=%s mode=%s (timeout=%ss)",
            model_name,
            mode.value,
            timeout_seconds,
        )

        try:
            # Asynchronous call with bounded timeout
            # SECURITY: Student code & prompts are not logged to stdout
            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=temperature,
                        max_output_tokens=1024,
                    ),
                ),
                timeout=timeout_seconds,
            )

            response_text = response.text or ""
            if not response_text.strip():
                raise AiProviderError("Gemini returned an empty response.")

            return AiResponse(
                content=response_text.strip(),
                mode=mode,
                model=model_name,
                provider="gemini",
                hint_level=request.hint_level if mode == AiMode.HINT else None,
            )

        except asyncio.TimeoutError:
            logger.warning("Gemini request timed out after %ss limit", timeout_seconds)
            raise AiTimeoutError(
                f"Gemini request timed out after {timeout_seconds}s. Please try again."
            )

        except APIError as exc:
            # Map Google API errors cleanly without leaking keys or raw stack traces
            err_msg = str(exc)
            logger.warning("Gemini APIError encountered: %s", exc.code if hasattr(exc, "code") else type(exc))

            if hasattr(exc, "code") and exc.code in (401, 403) or "API_KEY_INVALID" in err_msg:
                raise AiAuthenticationError("Invalid or unauthorized Gemini API key.")

            if hasattr(exc, "code") and exc.code == 429 or "RESOURCE_EXHAUSTED" in err_msg:
                raise AiQuotaError("Gemini API rate limit or quota exceeded. Please wait a moment.")

            raise AiProviderError(f"Gemini API returned an error: {exc.message if hasattr(exc, 'message') else 'Provider error'}")

        except (AiConfigurationError, AiAuthenticationError, AiQuotaError, AiTimeoutError):
            raise

        except Exception as exc:
            logger.exception("Unexpected error in GeminiProvider: %s", type(exc).__name__)
            raise AiProviderError("Failed to communicate with Gemini AI assistant.")


# Default provider instance
_provider_instance: Optional[GeminiProvider] = None


def get_ai_provider() -> BaseAiProvider:
    """Dependency provider returning AI provider adapter."""
    from app.services.ai.factory import get_ai_provider as _factory_get_provider
    return _factory_get_provider()
