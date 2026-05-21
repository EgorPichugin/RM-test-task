from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

from anthropic import Anthropic, AnthropicError

from src.config.settings import (
    FALLBACK_MODEL,
    LLM_MAX_RETRIES,
    LLM_MAX_INPUT_CHARS,
    LLM_MAX_TOKENS,
    LLM_REQUEST_TIMEOUT_SECONDS,
    LLM_RETRY_BACKOFF_SECONDS,
    LLM_TEMPERATURE,
)
from src.prompts import SYSTEM_PROMPT, build_prompt
from src.services.context_extractor import ExtractedContext
from src.services.llm_response_validator import (
    LlmResponseValidationError,
    LlmResponseValidator,
)

logger = logging.getLogger("AgentService")


class AgentServiceError(Exception):
    pass


@dataclass(frozen=True)
class AgentResult:
    findings: list[dict[str, Any]]


class AgentService:
    def __init__(
        self,
        anthropic_key: str,
        model: str,
        response_validator: LlmResponseValidator | None = None,
    ) -> None:
        self.model = model
        self.response_validator = response_validator or LlmResponseValidator()
        self.client = Anthropic(
            api_key=anthropic_key,
            timeout=LLM_REQUEST_TIMEOUT_SECONDS,
        )

    def find_missing_details(self, extracted_context: ExtractedContext) -> AgentResult:
        logger.info('Sending missing-details request to LLM model "%s"', self.model)

        prompt = build_prompt(
            transcript_text=extracted_context.transcript_text,
            crm_context=extracted_context.crm_context,
        )
        self._validate_prompt_size(prompt)

        response_text = self._send_with_fallback(prompt)

        findings = self._parse_and_validate_findings(
            response_text=response_text,
            transcript_text=extracted_context.transcript_text,
        )

        logger.info("LLM returned %s valid finding(s)", len(findings))
        return AgentResult(findings=findings)

    def _send_with_fallback(self, prompt: str) -> str:
        models_to_try = [self.model]
        if FALLBACK_MODEL != self.model:
            models_to_try.append(FALLBACK_MODEL)

        last_error: Exception | None = None
        for model in models_to_try:
            try:
                return self._send_with_retries(model=model, prompt=prompt)
            except AgentServiceError as error:
                last_error = error
                logger.error('LLM request failed for model "%s": %s', model, error)

        raise AgentServiceError("LLM request failed for all configured models") from last_error

    def _send_with_retries(self, model: str, prompt: str) -> str:
        for attempt in range(1, LLM_MAX_RETRIES + 1):
            try:
                logger.info(
                    'LLM request attempt %s/%s using model "%s"',
                    attempt,
                    LLM_MAX_RETRIES,
                    model,
                )
                response = self._create_message(model=model, prompt=prompt)
                return self._extract_response_text(response)
            except (AnthropicError, AgentServiceError) as error:
                if attempt == LLM_MAX_RETRIES:
                    logger.error("LLM request failed after retries: %s", error)
                    raise AgentServiceError("LLM request failed after retries") from error

                sleep_seconds = LLM_RETRY_BACKOFF_SECONDS * attempt
                logger.warning(
                    "Transient LLM request failure: %s. Retrying in %.1f second(s)",
                    error,
                    sleep_seconds,
                )
                time.sleep(sleep_seconds)

        raise AgentServiceError("LLM request failed")

    def _create_message(self, model: str, prompt: str) -> Any:
        return self.client.messages.create(
            model=model,
            max_tokens=LLM_MAX_TOKENS,
            temperature=LLM_TEMPERATURE,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

    def _parse_and_validate_findings(
        self,
        response_text: str,
        transcript_text: str,
    ) -> list[dict[str, Any]]:
        try:
            response_data = self._parse_response_json(response_text)
            return self.response_validator.validate(
                response_data=response_data,
                transcript_text=transcript_text,
            )
        except (AgentServiceError, LlmResponseValidationError) as error:
            logger.warning("LLM response validation failed. Requesting JSON repair: %s", error)
            try:
                repaired_response_text = self._request_json_repair(
                    invalid_response_text=response_text,
                    validation_error=str(error),
                )
                response_data = self._parse_response_json(repaired_response_text)
                return self.response_validator.validate(
                    response_data=response_data,
                    transcript_text=transcript_text,
                )
            except (AnthropicError, AgentServiceError, LlmResponseValidationError) as repair_error:
                logger.error("LLM JSON repair failed: %s", repair_error)
                raise AgentServiceError("LLM JSON repair failed") from repair_error

    def _request_json_repair(
        self,
        invalid_response_text: str,
        validation_error: str,
    ) -> str:
        repair_prompt = f"""
Your previous response was invalid.

Validation error:
{validation_error}

Rewrite the response as valid JSON only, using the exact required schema.
Do not add markdown or explanations.

Previous response:
{invalid_response_text}
""".strip()
        response = self._create_message(model=self.model, prompt=repair_prompt)
        return self._extract_response_text(response)

    @staticmethod
    def _validate_prompt_size(prompt: str) -> None:
        if len(prompt) > LLM_MAX_INPUT_CHARS:
            logger.error(
                "LLM prompt is too large: %s characters. Maximum allowed: %s",
                len(prompt),
                LLM_MAX_INPUT_CHARS,
            )
            raise AgentServiceError("LLM prompt is too large")

    @staticmethod
    def _extract_response_text(response: Any) -> str:
        text_parts: list[str] = []

        for content_block in getattr(response, "content", []):
            if getattr(content_block, "type", None) == "text":
                text_parts.append(getattr(content_block, "text", ""))

        response_text = "".join(text_parts).strip()
        if not response_text:
            logger.error("LLM response did not contain text content")
            raise AgentServiceError("LLM response did not contain text content")

        logger.info("Raw LLM response: %s", response_text)
        return response_text

    @staticmethod
    def _parse_response_json(response_text: str) -> dict[str, Any]:
        normalized_response_text = AgentService._normalize_response_text(response_text)

        try:
            parsed_response = json.loads(normalized_response_text)
        except json.JSONDecodeError as error:
            logger.error("LLM response is not valid JSON: %s", error)
            raise AgentServiceError("LLM response is not valid JSON") from error

        if not isinstance(parsed_response, dict):
            logger.error("LLM response JSON root must be an object")
            raise AgentServiceError("LLM response JSON root must be an object")

        return parsed_response

    @staticmethod
    def _normalize_response_text(response_text: str) -> str:
        clean_text = response_text.strip()

        if clean_text.startswith("```"):
            lines = clean_text.splitlines()
            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            clean_text = "\n".join(lines).strip()
            logger.info("Removed markdown code fence from LLM response")

        json_start = clean_text.find("{")
        json_end = clean_text.rfind("}")

        if json_start == -1 or json_end == -1 or json_end < json_start:
            return clean_text

        normalized_text = clean_text[json_start : json_end + 1].strip()
        if normalized_text != clean_text:
            logger.info("Extracted JSON object from LLM response text")

        return normalized_text
