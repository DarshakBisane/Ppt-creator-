"""Gemini AI Provider implementation using modern google-genai SDK."""

import asyncio
import logging
import time
from typing import Any

from google import genai
from google.genai import types
from google.genai.errors import APIError

from backend.app.ai.context import PresentationGenerationRequest
from backend.app.ai.exceptions import (
    AIConfigurationError,
    AIOutputValidationError,
    AIProviderError,
    AIProviderRateLimitError,
    AIProviderTimeoutError,
)
from backend.app.ai.prompts import PromptBuilder
from backend.app.ai.provider import AIProvider
from backend.app.ai.recovery import OnePassRecoveryHandler
from backend.app.config import get_settings
from backend.app.domain.presentation import Presentation

logger = logging.getLogger("app.ai.gemini")

MAX_GENERATION_ATTEMPTS = 2


class GeminiProvider(AIProvider):
    """Production Gemini presentation generation provider with 1-pass recovery."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
        max_attempts: int = MAX_GENERATION_ATTEMPTS,
        client: Any | None = None,
    ) -> None:
        settings = get_settings()
        self._api_key = api_key or settings.gemini_api_key
        self.model = model or settings.gemini_model
        self.timeout_seconds = timeout_seconds or float(settings.ai_timeout_seconds)
        self.max_attempts = min(max(1, max_attempts), 2)  # Strictly bounded to max 2 attempts

        self._client = client

    @property
    def client(self) -> genai.Client:
        """Lazily initialize and return the google-genai Client."""
        if self._client is None:
            if not self._api_key or not self._api_key.strip():
                raise AIConfigurationError(
                    "Gemini API key is not configured. Please set GEMINI_API_KEY in the environment."
                )
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    async def _execute_model_call(self, system_instruction: str, prompt: str) -> str:
        """Execute async generation call against Gemini API with strict timeout and structured schema."""
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=Presentation,
            temperature=0.7,
        )

        try:
            start_time = time.perf_counter()
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=config,
                ),
                timeout=self.timeout_seconds,
            )
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                "Gemini call completed successfully",
                extra={
                    "model": self.model,
                    "duration_ms": round(duration_ms, 2),
                },
            )

            raw_text = response.text or ""
            if not raw_text.strip():
                raise AIProviderError("Gemini returned empty response text.")
            return raw_text

        except (asyncio.TimeoutError, TimeoutError) as exc:
            logger.error("Gemini call timed out after %s seconds", self.timeout_seconds)
            raise AIProviderTimeoutError(
                f"AI generation timed out after {self.timeout_seconds} seconds."
            ) from exc

        except APIError as api_err:
            status_code = getattr(api_err, "code", None)
            err_msg = str(api_err)
            logger.error("Gemini APIError encountered: code=%s, message=%s", status_code, err_msg)

            if status_code == 429 or "RESOURCE_EXHAUSTED" in err_msg.upper() or "429" in err_msg:
                raise AIProviderRateLimitError("Gemini rate limit or quota exceeded.") from api_err

            raise AIProviderError(f"Gemini API error occurred: {err_msg}") from api_err

        except (AIProviderError, AIConfigurationError):
            raise

        except Exception as unhandled:
            logger.error("Unexpected error in Gemini generation: %s", str(unhandled))
            raise AIProviderError(f"Unexpected error communicating with AI provider: {str(unhandled)}") from unhandled

    async def generate_presentation(
        self,
        request: PresentationGenerationRequest,
    ) -> Presentation:
        """Generate a validated Presentation domain model with 1-pass auto-recovery."""
        system_instruction = PromptBuilder.build_system_instruction()
        initial_prompt = PromptBuilder.build_user_prompt(request)

        last_error_summary: str | None = None
        last_raw_text: str = ""

        for attempt in range(1, self.max_attempts + 1):
            logger.info(
                "Initiating AI presentation generation attempt %d/%d for topic: %s",
                attempt,
                self.max_attempts,
                request.topic[:50],
            )

            if attempt == 1:
                prompt_to_send = initial_prompt
            else:
                prompt_to_send = PromptBuilder.build_repair_prompt(
                    request=request,
                    raw_output=last_raw_text,
                    validation_errors=last_error_summary or "Schema validation failed.",
                )

            raw_text = await self._execute_model_call(
                system_instruction=system_instruction,
                prompt=prompt_to_send,
            )
            last_raw_text = raw_text

            presentation, error_summary = OnePassRecoveryHandler.parse_and_validate(raw_text)

            if presentation is not None:
                logger.info("AI presentation generation validated successfully on attempt %d", attempt)
                return presentation

            last_error_summary = error_summary
            logger.warning(
                "Attempt %d output failed domain validation. Error summary: %s",
                attempt,
                error_summary,
            )

        # If we exhausted all attempts
        raise AIOutputValidationError(
            message=f"AI output validation failed after {self.max_attempts} attempts.",
            details=[{"summary": last_error_summary or "Invalid schema structure"}],
        )
