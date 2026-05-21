from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from src.models.external_data import (
    AircallData,
    SmartMovingCharge,
    SmartMovingData,
    SmartMovingInventory,
    SmartMovingJob,
    SmartMovingNotes,
    SmartMovingStop,
)

logger = logging.getLogger("ContextExtractor")


class EDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class ContextExtractionError(Exception):
    """Raised when context extraction fails because of invalid input data."""


@dataclass(frozen=True)
class ExtractedContext:
    direction: EDirection
    duration: int | None
    transcript_text: str
    crm_context: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "direction": self.direction.value,
            "duration": self.duration,
            "transcript_text": self.transcript_text,
            "crm_context": self.crm_context,
        }


class ContextExtractor:
    """
    Builds a compact context for the LLM.

    Important design choice:
    - The extractor does not decide whether a call should be analyzed.
    - Missing or empty transcript is not treated as an error here.
    - PreCheckService should decide whether to return {"findings": []}.
    """

    IMPORTANT_CHARGE_NAMES = {
        "Heavy Items Fee",
        "Full Value Protection",
        "Materials & Packing Supplies",
        "Estimated Move Day Total",
    }

    def extract(
        self,
        aircall_data: AircallData,
        smartmoving_data: SmartMovingData,
    ) -> ExtractedContext:
        logger.info("Extracting compact context from Aircall and SmartMoving objects")

        direction = self._extract_direction(aircall_data)
        transcript_text = self._extract_transcript_text(aircall_data)
        crm_context = self._extract_crm_context(smartmoving_data)

        logger.info("Call direction: %s", direction.value)
        logger.info("Transcript length: %s characters", len(transcript_text))
        logger.info("CRM context extracted for quote %s", crm_context.get("quote_number"))

        return ExtractedContext(
            direction=direction,
            duration=aircall_data.duration,
            transcript_text=transcript_text,
            crm_context=crm_context,
        )

    @staticmethod
    def _extract_direction(aircall_data: AircallData) -> EDirection:
        try:
            return EDirection(aircall_data.direction)
        except ValueError as exc:
            raise ContextExtractionError(
                f"Unsupported Aircall direction: {aircall_data.direction!r}"
            ) from exc

    def _extract_transcript_text(self, aircall_data: AircallData) -> str:
        utterances = self._get_utterances(aircall_data)

        if not utterances:
            logger.info("Aircall transcript is missing or empty")
            return ""

        transcript_lines: list[str] = []

        for utterance in utterances:
            speaker = self._normalize_speaker(getattr(utterance, "speaker", None))
            text = str(getattr(utterance, "text", "") or "").strip()

            if not text:
                logger.debug("Skipping empty utterance for speaker %s", speaker)
                continue

            transcript_lines.append(f"{speaker}: {text}")

        return "\n".join(transcript_lines)

    @staticmethod
    def _get_utterances(aircall_data: AircallData) -> list[Any]:
        """Safely retrieves transcription.content.utterances."""
        transcription = getattr(aircall_data, "transcription", None)
        if transcription is None:
            return []

        content = getattr(transcription, "content", None)
        if content is None:
            return []

        utterances = getattr(content, "utterances", None)
        return utterances or []

    @staticmethod
    def _normalize_speaker(speaker: Any) -> str:
        value = str(speaker or "unknown").strip().lower() or "unknown"

        if value == "external":
            return "customer"

        if value == "agent":
            return "agent"

        return value

    def _extract_crm_context(self, smartmoving_data: SmartMovingData) -> dict[str, Any]:
        """Extracts only operationally useful CRM fields for the LLM."""
        return {
            "quote_number": smartmoving_data.quote_number,
            "status": smartmoving_data.status_name,
            "service_date": smartmoving_data.service_date,
            "move_size": smartmoving_data.move_size,
            "estimated_total": smartmoving_data.estimated_total,
            "customer": self._extract_customer(smartmoving_data),
            "jobs": [self._extract_job(job) for job in smartmoving_data.jobs],
        }

    @staticmethod
    def _extract_customer(data: SmartMovingData) -> dict[str, Any]:
        customer = data.customer
        return {
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "phone_number": customer.phone_number,
            "email_address": customer.email_address,
        }

    def _extract_job(self, job: SmartMovingJob) -> dict[str, Any]:
        return {
            "job_number": job.job_number,
            "type": job.type_name,
            "service_date": job.service_date,
            "confirmed": job.confirmed,
            "scheduled": job.scheduled,
            "arrival_window": job.arrival_window,
            "estimated_duration": job.estimated_duration,
            "crew_size": job.crew_size,
            "truck_count": job.truck_count,
            "stops": self._extract_stops(job.stops),
            "notes": self._extract_notes(job.notes),
            "charges": self._extract_charges(job.charges),
            "inventory": self._extract_inventory(job.inventory),
        }

    @staticmethod
    def _extract_stops(stops: list[SmartMovingStop]) -> list[dict[str, Any]]:
        return [
            {
                "order": stop.order,
                "type": stop.type,
                "address": stop.address_full_address,
                "unit": stop.address_unit,
                "property_type": stop.property_type_name,
                "stairs": stop.stairs,
                "has_elevator": stop.has_elevator,
                "parking": stop.parking_description,
                "notes": stop.notes,
            }
            for stop in stops
        ]

    @staticmethod
    def _extract_notes(notes: SmartMovingNotes) -> dict[str, Any]:
        return {
            "internal": notes.internal_notes,
            "customer": notes.customer_notes,
            "crew": notes.crew_notes,
            "dispatcher": notes.dispatcher_notes,
            "accounting": notes.accounting_notes,
        }

    def _extract_charges(self, charges: list[SmartMovingCharge]) -> list[dict[str, Any]]:
        """Keeps only charges that help detect missing operational facts."""
        return [
            {
                "name": charge.name,
                "rate": charge.rate,
                "total_cost": charge.total_cost,
            }
            for charge in charges
            if charge.name in self.IMPORTANT_CHARGE_NAMES
        ]

    @staticmethod
    def _extract_inventory(inventory: SmartMovingInventory) -> dict[str, Any]:
        return {
            "total_volume_cu_ft": inventory.total_volume_cu_ft,
            "total_weight_lbs": inventory.total_weight_lbs,
            "rooms": [
                {
                    "name": room.name,
                    "item_count": room.item_count,
                }
                for room in inventory.rooms
            ],
            "items": [
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "estimated_weight_lbs": item.estimated_weight_lbs,
                }
                for item in inventory.items
            ],
        }
