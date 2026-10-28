"""Abstract base class for AI model provider adapters."""

from abc import ABC, abstractmethod

from app.services.ai.models import AiMode, AiRequest, AiResponse


class BaseAiProvider(ABC):
    """Interface for AI model providers (Gemini, local models, etc.)."""

    @abstractmethod
    async def generate_response(
        self, request: AiRequest, mode: AiMode
    ) -> AiResponse:
        """Generate response for explain or hint requests."""
        raise NotImplementedError
