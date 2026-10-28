"""OpenAI AI Provider Adapter using official openai SDK."""

import asyncio
import logging
from typing import Optional

import openai
from openai import AsyncOpenAI

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


class OpenAiProvider(BaseAiProvider):
    """Adapter for OpenAI models using official AsyncOpenAI SDK."""

    def __init__(self, client: Optional[AsyncOpenAI] = None):
        self._client = client

    def _get_client(self) -> AsyncOpenAI:
        """Lazily initialize or return the AsyncOpenAI client."""
        if self._client is not None:
            return self._client

        settings = get_settings()

        if not settings.AI_ASSISTANT_ENABLED:
            raise AiConfigurationError(
                "AI Assistant is currently disabled. Set AI_ASSISTANT_ENABLED=true in .env to enable."
            )

        api_key = settings.OPENAI_API_KEY
        if (
            not api_key
            or not api_key.strip()
            or "your-openai-api-key" in api_key.lower()
            or api_key.strip() == '""'
        ):
            raise AiConfigurationError(
                "OpenAI API key is not configured. Set OPENAI_API_KEY in your .env file to enable OpenAI assistance."
            )

        if self._client is None:
            self._client = AsyncOpenAI(api_key=api_key.strip())

        return self._client

    async def generate_response(
        self, request: AiRequest, mode: AiMode
    ) -> AiResponse:
        """Call OpenAI model asynchronously with strict timeouts and error mapping."""
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

        model_name = settings.OPENAI_MODEL
        timeout_seconds = settings.OPENAI_TIMEOUT_SECONDS

        logger.info(
            "Calling OpenAI model=%s mode=%s (timeout=%ss)",
            model_name,
            mode.value,
            timeout_seconds,
        )

        try:
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model=model_name,
                    max_tokens=1024,
                    temperature=temperature,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_prompt},
                    ],
                ),
                timeout=timeout_seconds,
            )

            content_text = ""
            if response.choices and response.choices[0].message:
                content_text = response.choices[0].message.content or ""

            if not content_text.strip():
                raise AiProviderError("OpenAI returned an empty response.")

            return AiResponse(
                content=content_text.strip(),
                mode=mode,
                model=model_name,
                provider="openai",
                hint_level=request.hint_level if mode == AiMode.HINT else None,
            )

        except (asyncio.TimeoutError, openai.APITimeoutError):
            logger.warning("OpenAI request timed out after %ss limit", timeout_seconds)
            raise AiTimeoutError(
                f"OpenAI request timed out after {timeout_seconds}s. Please try again."
            )

        except openai.AuthenticationError as exc:
            logger.warning("OpenAI authentication failed: %s", type(exc).__name__)
            raise AiAuthenticationError("Invalid or unauthorized OpenAI API key.")

        except openai.RateLimitError as exc:
            logger.warning("OpenAI rate limit exceeded: %s", type(exc).__name__)
            raise AiQuotaError("OpenAI API rate limit or quota exceeded. Please wait a moment.")

        except openai.APIError as exc:
            err_msg = getattr(exc, "message", str(exc))
            logger.warning("OpenAI APIError encountered: %s", type(exc).__name__)
            raise AiProviderError(f"OpenAI API returned an error: {err_msg}")

        except (AiConfigurationError, AiAuthenticationError, AiQuotaError, AiTimeoutError):
            raise

        except Exception as exc:
            logger.exception("Unexpected error in OpenAiProvider: %s", type(exc).__name__)
            raise AiProviderError("Failed to communicate with OpenAI assistant.")
