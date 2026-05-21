from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from src.services.context_extractor import EDirection, ExtractedContext

logger = logging.getLogger("PreCheckService")


class PreCheckStatus(str, Enum):
    PASSED = "passed"
    EMPTY_FINDINGS = "empty_findings"


@dataclass(frozen=True)
class PreCheckResult:
    status: PreCheckStatus
    warning_message: str | None = None

    @property
    def should_return_empty_findings(self) -> bool:
        return self.status == PreCheckStatus.EMPTY_FINDINGS

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "warning_message": self.warning_message,
        }


class PreCheckService:
    OUTBOUND_SHORT_CALL_DURATION_SECONDS = 30

    def check(self, extracted_context: ExtractedContext) -> PreCheckResult:
        logger.info("Running pre-checks before LLM analysis")

        if not extracted_context.transcript_text.strip():
            warning_message = "Findings are empty because Aircall transcript is empty"
            logger.warning(warning_message)
            return PreCheckResult(
                status=PreCheckStatus.EMPTY_FINDINGS,
                warning_message=warning_message,
            )

        if not self._has_crm_context(extracted_context.crm_context):
            warning_message = "Findings are empty because CRM context is empty"
            logger.warning(warning_message)
            return PreCheckResult(
                status=PreCheckStatus.EMPTY_FINDINGS,
                warning_message=warning_message,
            )

        if self._is_short_outbound_call(extracted_context):
            warning_message = (
                "Findings are empty because outbound call duration is less than "
                f"or equal to {self.OUTBOUND_SHORT_CALL_DURATION_SECONDS} seconds"
            )
            logger.warning(warning_message)
            return PreCheckResult(
                status=PreCheckStatus.EMPTY_FINDINGS,
                warning_message=warning_message,
            )

        logger.info("Pre-checks passed")
        return PreCheckResult(status=PreCheckStatus.PASSED)

    @staticmethod
    def _has_crm_context(crm_context: dict[str, Any]) -> bool:
        if not crm_context:
            return False

        return any(value not in (None, "", [], {}) for value in crm_context.values())

    def _is_short_outbound_call(self, extracted_context: ExtractedContext) -> bool:
        return (
            extracted_context.direction == EDirection.OUTBOUND
            and extracted_context.duration is not None
            and extracted_context.duration <= self.OUTBOUND_SHORT_CALL_DURATION_SECONDS
        )
