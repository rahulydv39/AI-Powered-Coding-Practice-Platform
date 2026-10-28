"""Automated test suite for Multi-Provider AI (Gemini, Claude, OpenAI)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.services.ai.base import BaseAiProvider
from app.services.ai.claude_provider import ClaudeProvider
from app.services.ai.exceptions import (
    AiAuthenticationError,
    AiConfigurationError,
    AiProviderError,
    AiQuotaError,
    AiTimeoutError,
)
from app.services.ai.factory import (
    SUPPORTED_PROVIDERS,
    get_ai_provider,
    get_available_providers,
)
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.models import AiMode, AiRequest, AiResponse
from app.services.ai.openai_provider import OpenAiProvider
from app.services.challenges.request_deduplication import (
    CHALLENGE_ID,
    REFERENCE_SOLUTION,
    STARTER_CODE,
)
from app.services.runner.docker_runner import DockerSandboxRunner
from app.services.runner.models import RunResult


# ==============================================================================
# Unit Tests: Provider Selection, Factory & Allowlist
# ==============================================================================

def test_supported_providers_allowlist() -> None:
    """Supported providers must include gemini, claude, and openai."""
    assert "gemini" in SUPPORTED_PROVIDERS
    assert "claude" in SUPPORTED_PROVIDERS
    assert "openai" in SUPPORTED_PROVIDERS


def test_get_available_providers_does_not_leak_keys() -> None:
    """Provider list must return metadata without leaking raw secrets or API keys."""
    providers = get_available_providers()
    assert len(providers) == 3
    provider_ids = [p["id"] for p in providers]
    assert "gemini" in provider_ids
    assert "claude" in provider_ids
    assert "openai" in provider_ids

    for p in providers:
        assert "id" in p
        assert "name" in p
        assert "model" in p
        assert "configured" in p
        assert isinstance(p["configured"], bool)
        # Ensure no key field exists
        assert "key" not in p
        assert "api_key" not in p
        assert "secret" not in p


def test_factory_returns_correct_adapter_types() -> None:
    """Factory correctly instantiates corresponding provider adapters."""
    gemini = get_ai_provider("gemini")
    assert isinstance(gemini, GeminiProvider)

    claude = get_ai_provider("claude")
    assert isinstance(claude, ClaudeProvider)

    openai = get_ai_provider("openai")
    assert isinstance(openai, OpenAiProvider)


def test_factory_rejects_unsupported_provider() -> None:
    """Unsupported provider names must raise AiConfigurationError and not fall back silently."""
    with pytest.raises(AiConfigurationError) as exc_info:
        get_ai_provider("unsupported-llm-xyz")
    assert "unsupported" in str(exc_info.value).lower()
    assert "gemini, claude, openai" in str(exc_info.value).lower()


# ==============================================================================
# Unit Tests: No Silent Fallback & Missing Key Behavior
# ==============================================================================

@pytest.mark.asyncio
async def test_claude_missing_key_raises_configuration_error_without_fallback() -> None:
    """When Claude key is missing, raises specific Anthropic error, NOT silently switching to Gemini."""
    settings = get_settings()
    original_key = settings.ANTHROPIC_API_KEY
    settings.ANTHROPIC_API_KEY = ""
    try:
        provider = ClaudeProvider()
        req = AiRequest(code="def foo(): pass", challenge_title="Test", challenge_description="Desc")
        with pytest.raises(AiConfigurationError) as exc:
            await provider.generate_response(req, mode=AiMode.EXPLAIN)
        assert "anthropic api key is not configured" in str(exc.value).lower()
    finally:
        settings.ANTHROPIC_API_KEY = original_key


@pytest.mark.asyncio
async def test_openai_missing_key_raises_configuration_error_without_fallback() -> None:
    """When OpenAI key is missing, raises specific OpenAI error, NOT silently switching to Gemini."""
    settings = get_settings()
    original_key = settings.OPENAI_API_KEY
    settings.OPENAI_API_KEY = ""
    try:
        provider = OpenAiProvider()
        req = AiRequest(code="def foo(): pass", challenge_title="Test", challenge_description="Desc")
        with pytest.raises(AiConfigurationError) as exc:
            await provider.generate_response(req, mode=AiMode.EXPLAIN)
        assert "openai api key is not configured" in str(exc.value).lower()
    finally:
        settings.OPENAI_API_KEY = original_key


# ==============================================================================
# Unit Tests: Claude Adapter Error Mapping
# ==============================================================================

@pytest.mark.asyncio
async def test_claude_adapter_success_flow() -> None:
    """Claude adapter properly maps SDK response to normalized AiResponse."""
    mock_client = AsyncMock()
    mock_block = MagicMock()
    mock_block.text = "### Overview\nClaude explanation text."
    mock_response = MagicMock()
    mock_response.content = [mock_block]
    mock_client.messages.create.return_value = mock_response

    provider = ClaudeProvider(client=mock_client)
    req = AiRequest(code="def foo(): pass", challenge_title="Test", challenge_description="Desc")
    resp = await provider.generate_response(req, mode=AiMode.EXPLAIN)

    assert resp.content == "### Overview\nClaude explanation text."
    assert resp.provider == "claude"
    assert resp.mode == AiMode.EXPLAIN


@pytest.mark.asyncio
async def test_claude_adapter_timeout_error() -> None:
    """Claude adapter converts timeout into AiTimeoutError."""
    import anthropic

    mock_client = AsyncMock()
    mock_client.messages.create.side_effect = anthropic.APITimeoutError(request=MagicMock())

    provider = ClaudeProvider(client=mock_client)
    req = AiRequest(code="def foo(): pass", challenge_title="Test", challenge_description="Desc")

    with pytest.raises(AiTimeoutError) as exc:
        await provider.generate_response(req, mode=AiMode.EXPLAIN)
    assert "timed out" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_claude_adapter_auth_and_quota_errors() -> None:
    """Claude adapter properly maps 401/403 and 429 into AiAuthenticationError and AiQuotaError."""
    import anthropic

    mock_client = AsyncMock()
    mock_client.messages.create.side_effect = anthropic.AuthenticationError(
        message="Invalid API Key", response=MagicMock(), body={}
    )
    provider = ClaudeProvider(client=mock_client)
    req = AiRequest(code="def foo(): pass", challenge_title="Test", challenge_description="Desc")

    with pytest.raises(AiAuthenticationError):
        await provider.generate_response(req, mode=AiMode.EXPLAIN)

    mock_client.messages.create.side_effect = anthropic.RateLimitError(
        message="Rate limit exceeded", response=MagicMock(), body={}
    )
    with pytest.raises(AiQuotaError):
        await provider.generate_response(req, mode=AiMode.EXPLAIN)


# ==============================================================================
# Unit Tests: OpenAI Adapter Error Mapping
# ==============================================================================

@pytest.mark.asyncio
async def test_openai_adapter_success_flow() -> None:
    """OpenAI adapter properly maps SDK completion to normalized AiResponse."""
    mock_client = AsyncMock()
    mock_message = MagicMock()
    mock_message.content = "### Overview\nOpenAI explanation."
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_completion

    provider = OpenAiProvider(client=mock_client)
    req = AiRequest(code="def foo(): pass", challenge_title="Test", challenge_description="Desc")
    resp = await provider.generate_response(req, mode=AiMode.EXPLAIN)

    assert resp.content == "### Overview\nOpenAI explanation."
    assert resp.provider == "openai"
    assert resp.mode == AiMode.EXPLAIN


@pytest.mark.asyncio
async def test_openai_adapter_timeout_and_auth_errors() -> None:
    """OpenAI adapter properly maps timeouts and auth failures."""
    import openai

    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = openai.APITimeoutError(request=MagicMock())

    provider = OpenAiProvider(client=mock_client)
    req = AiRequest(code="def foo(): pass", challenge_title="Test", challenge_description="Desc")

    with pytest.raises(AiTimeoutError):
        await provider.generate_response(req, mode=AiMode.EXPLAIN)

    mock_client.chat.completions.create.side_effect = openai.AuthenticationError(
        message="Incorrect API key provided", response=MagicMock(), body={}
    )
    with pytest.raises(AiAuthenticationError):
        await provider.generate_response(req, mode=AiMode.EXPLAIN)


# ==============================================================================
# Integration Tests: Endpoints with Provider Selection
# ==============================================================================

def test_api_list_ai_providers_endpoint(client: TestClient) -> None:
    """GET /api/v1/challenges/ai/providers returns supported provider list."""
    response = client.get("/api/v1/challenges/ai/providers")
    assert response.status_code == 200
    data = response.json()

    assert "default_provider" in data
    assert "providers" in data
    assert len(data["providers"]) == 3
    ids = [p["id"] for p in data["providers"]]
    assert "gemini" in ids
    assert "claude" in ids
    assert "openai" in ids


def test_api_explain_rejects_unsupported_provider(client: TestClient) -> None:
    """Requesting an unsupported provider must return HTTP 400 Bad Request."""
    response = client.post(
        f"/api/v1/challenges/{CHALLENGE_ID}/ai/explain",
        json={"code": STARTER_CODE, "provider": "deepseek-r1"},
    )
    assert response.status_code == 400
    assert "unsupported ai provider" in response.json()["error"]["message"].lower()


def test_api_hint_rejects_unsupported_provider(client: TestClient) -> None:
    """Requesting an unsupported provider in hint must return HTTP 400."""
    response = client.post(
        f"/api/v1/challenges/{CHALLENGE_ID}/ai/hint",
        json={"code": STARTER_CODE, "hint_level": 1, "provider": "invalid-provider"},
    )
    assert response.status_code == 400


def test_api_review_rejects_unsupported_provider(client: TestClient) -> None:
    """Requesting an unsupported provider in review must return HTTP 400."""
    mock_run = RunResult(
        status="passed",
        passed=5,
        failed=0,
        total=5,
        execution_time_ms=100.0,
        docker_available=True,
    )
    with patch.object(DockerSandboxRunner, "run_submission", return_value=mock_run):
        sub_resp = client.post(
            f"/api/v1/challenges/{CHALLENGE_ID}/submit",
            json={"code": REFERENCE_SOLUTION},
        )
        submission_id = sub_resp.json()["submission_id"]

    response = client.get(
        f"/api/v1/challenges/{CHALLENGE_ID}/submissions/{submission_id}/review?include_ai=true&provider=unsupported-llm"
    )
    assert response.status_code == 400
    assert "unsupported ai provider" in response.json()["error"]["message"].lower()


def test_api_ai_responses_do_not_leak_secrets(client: TestClient) -> None:
    """AI endpoint responses must never contain secret keys or sensitive env data."""
    response = client.get("/api/v1/challenges/ai/providers")
    body = response.text
    assert "sk-" not in body
    assert "API_KEY" not in body
    assert "AI_RATE_LIMIT" not in body
