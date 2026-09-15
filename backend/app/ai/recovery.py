"""Validation and 1-pass recovery handler for AI presentation generation."""

import json
import logging
from typing import Any
from pydantic import ValidationError

from backend.app.domain.presentation import Presentation

logger = logging.getLogger("app.ai.recovery")


class OnePassRecoveryHandler:
    """Handles JSON parsing, Pydantic schema validation, and error summarization for 1-pass recovery."""

    @staticmethod
    def parse_and_validate(raw_content: str | dict[str, Any]) -> tuple[Presentation | None, str | None]:
        """Attempt to validate the raw AI response against the Presentation domain model.

        Returns:
            tuple[Presentation | None, str | None]: (validated_presentation, None) on success,
            or (None, formatted_error_summary) on failure.
        """
        try:
            if isinstance(raw_content, dict):
                presentation = Presentation.model_validate(raw_content)
            elif isinstance(raw_content, str):
                cleaned_text = raw_content.strip()
                # Strip markdown code blocks if the provider wrapped JSON in ```json ... ```
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                elif cleaned_text.startswith("```"):
                    cleaned_text = cleaned_text[3:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()

                presentation = Presentation.model_validate_json(cleaned_text)
            else:
                return None, f"Unexpected response type: {type(raw_content).__name__}"

            return presentation, None

        except json.JSONDecodeError as json_err:
            error_msg = f"Malformed JSON output: {str(json_err)}"
            logger.warning("AI output JSON decode error: %s", error_msg)
            return None, error_msg

        except ValidationError as val_err:
            errors = val_err.errors()
            formatted_errors = []
            for err in errors[:10]:  # Limit to top 10 errors to keep repair prompt concise
                loc = " -> ".join(str(item) for item in err.get("loc", []))
                msg = err.get("msg", "invalid")
                err_type = err.get("type", "")
                formatted_errors.append(f"- Location '{loc}': {msg} ({err_type})")

            error_summary = "\n".join(formatted_errors)
            logger.warning("AI output Pydantic validation failed with %d error(s):\n%s", len(errors), error_summary)
            return None, error_summary

        except Exception as exc:
            error_msg = f"Unexpected validation exception: {str(exc)}"
            logger.warning("AI output validation failure: %s", error_msg)
            return None, error_msg
