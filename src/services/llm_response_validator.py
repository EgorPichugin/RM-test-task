from __future__ import annotations

import logging
from typing import Any

from src.prompts import ALLOWED_CATEGORIES

logger = logging.getLogger("LlmResponseValidator")


class LlmResponseValidationError(Exception):
    pass


class LlmResponseValidator:
    ALLOWED_CONFIDENCE_VALUES = {"high", "medium", "low"}

    def validate(
        self,
        response_data: dict[str, Any],
        transcript_text: str,
    ) -> list[dict[str, Any]]:
        findings = response_data.get("findings")
        if not isinstance(findings, list):
            logger.error('LLM response JSON is missing a valid "findings" list')
            raise LlmResponseValidationError(
                'LLM response JSON is missing a valid "findings" list'
            )

        validated_findings: list[dict[str, Any]] = []
        for index, finding in enumerate(findings):
            validated_findings.append(
                self._validate_finding(
                    finding=finding,
                    index=index,
                    transcript_text=transcript_text,
                )
            )

        logger.info("Validated %s LLM finding(s)", len(validated_findings))
        return validated_findings

    def _validate_finding(
        self,
        finding: Any,
        index: int,
        transcript_text: str,
    ) -> dict[str, Any]:
        if not isinstance(finding, dict):
            raise LlmResponseValidationError(f"Finding #{index + 1} must be an object")

        category = self._require_string(finding, "category", index)
        summary = self._require_string(finding, "summary", index)
        quote = self._require_string(finding, "quote", index)
        confidence = self._require_string(finding, "confidence", index).casefold()

        if category not in ALLOWED_CATEGORIES:
            raise LlmResponseValidationError(
                f'Finding #{index + 1} has unsupported category "{category}"'
            )

        if confidence not in self.ALLOWED_CONFIDENCE_VALUES:
            raise LlmResponseValidationError(
                f'Finding #{index + 1} has unsupported confidence "{confidence}"'
            )

        quote_verified = quote in transcript_text
        if not quote_verified:
            logger.warning(
                "Finding #%s quote is not present verbatim in transcript",
                index + 1,
            )

        return {
            "category": category,
            "summary": summary,
            "quote": quote,
            "confidence": confidence,
            "quote_verified": quote_verified,
        }

    @staticmethod
    def _require_string(finding: dict[str, Any], field_name: str, index: int) -> str:
        value = finding.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise LlmResponseValidationError(
                f'Finding #{index + 1} is missing non-empty "{field_name}"'
            )

        return value.strip()
