"""Anthropic Claude AI Provider Adapter using official anthropic SDK."""

import asyncio
import logging
from typing import Optional

import anthropic
from anthropic import AsyncAnthropic

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


class ClaudeProvider(BaseAiProvider):
    """Adapter for Anthropic Claude using official AsyncAnthropic SDK."""

    def __init__(self, client: Optional[AsyncAnthropic] = None):
        self._client = client

    def _get_client(self) -> AsyncAnthropic:
        """Lazily initialize or return the AsyncAnthropic client."""
        if self._client is not None:
            return self._client

        settings = get_settings()

        if not settings.AI_ASSISTANT_ENABLED:
            raise AiConfigurationError(
                "AI Assistant is currently disabled. Set AI_ASSISTANT_ENABLED=true in .env to enable."
            )

        api_key = settings.ANTHROPIC_API_KEY
        if (
            not api_key
            or not api_key.strip()
            or "your-anthropic-api-key" in api_key.lower()
            or api_key.strip() == '""'
        ):
            raise AiConfigurationError(
                "Anthropic API key is not configured. Set ANTHROPIC_API_KEY in your .env file to enable Claude AI assistance."
            )

        if self._client is None:
            self._client = AsyncAnthropic(api_key=api_key.strip())

        return self._client

    async def generate_response(
        self, request: AiRequest, mode: AiMode
    ) -> AiResponse:
        """Call Claude model asynchronously with strict timeouts and error mapping."""
        settings = get_settings()
        client = self._get_client()

        if mode == AiMode.EXPLAIN:
            system_instruction = EXPLAIN_SYSTEM_INSTRUCTION
        elif mode == AiMode.HINT:
            system_instruction = HINT_SYSTEM_INSTRUCTION
        else:
            system_instruction = REVIEW_SYSTEM_INSTRUCTION

        user_prompt = build_user_prompt(request, mode)

        if mode == AiMode.HINT:
            temperature = 0.2
        elif mode == AiMode.REVIEW:
            temperature = 0.3
        else:
            temperature = 0.4

        model_name = settings.ANTHROPIC_MODEL
        timeout_seconds = settings.ANTHROPIC_TIMEOUT_SECONDS

        logger.info(
            "Calling Claude model=%s mode=%s (timeout=%ss)",
            model_name,
            mode.value,
            timeout_seconds,
        )

        try:
            response = await asyncio.wait_for(
                client.messages.create(
                    model=model_name,
                    max_tokens=1024,
                    temperature=temperature,
                    system=system_instruction,
                    messages=[
                        {"role": "user", "content": user_prompt},
                    ],
                ),
                timeout=timeout_seconds,
            )

            # Extract response text safely
            content_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    content_text += block.text

            if not content_text.strip():
                raise AiProviderError("Claude returned an empty response.")

            return AiResponse(
                content=content_text.strip(),
                mode=mode,
                model=model_name,
                provider="claude",
                hint_level=request.hint_level if mode == AiMode.HINT else None,
            )

        except (asyncio.TimeoutError, anthropic.APITimeoutError):
            logger.warning("Claude request timed out after %ss limit", timeout_seconds)
            raise AiTimeoutError(
                f"Anthropic request timed out after {timeout_seconds}s. Please try again."
            )

        except anthropic.AuthenticationError as exc:
            logger.warning("Claude authentication failed: %s", type(exc).__name__)
            raise AiAuthenticationError("Invalid or unauthorized Anthropic API key.")

        except anthropic.RateLimitError as exc:
            logger.warning("Claude rate limit exceeded: %s", type(exc).__name__)
            raise AiQuotaError("Anthropic API rate limit or quota exceeded. Please wait a moment.")

        except anthropic.APIError as exc:
            err_msg = getattr(exc, "message", str(exc))
            logger.warning("Claude APIError encountered: %s", type(exc).__name__)
            raise AiProviderError(f"Anthropic API returned an error: {err_msg}")

        except (AiConfigurationError, AiAuthenticationError, AiQuotaError, AiTimeoutError):
            raise

        except Exception as exc:
            logger.exception("Unexpected error in ClaudeProvider: %s", type(exc).__name__)
            raise AiProviderError("Failed to communicate with Anthropic Claude AI assistant.")
