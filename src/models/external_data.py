from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AircallPhoneNumber:
    label: str | None
    value: str | None


@dataclass(frozen=True)
class AircallEmail:
    label: str | None
    value: str | None


@dataclass(frozen=True)
class AircallNumber:
    id: int | None
    name: str | None
    digits: str | None
    country: str | None


@dataclass(frozen=True)
class AircallUser:
    id: int | None
    name: str | None
    email: str | None
    available: bool | None


@dataclass(frozen=True)
class AircallContact:
    id: int | None
    first_name: str | None
    last_name: str | None
    company_name: str | None
    phone_numbers: list[AircallPhoneNumber]
    emails: list[AircallEmail]


@dataclass(frozen=True)
class AircallTranscriptChannel:
    speaker: str | None
    name: str | None


@dataclass(frozen=True)
class AircallUtterance:
    start: float | int | None
    end: float | int | None
    speaker: str | None
    text: str | None


@dataclass(frozen=True)
class AircallTranscriptContent:
    channels: list[AircallTranscriptChannel]
    utterances: list[AircallUtterance]


@dataclass(frozen=True)
class AircallTranscription:
    id: int | None
    call_id: int | None
    language: str | None
    created_at: int | None
    content: AircallTranscriptContent


@dataclass(frozen=True)
class AircallData:
    id: int | None
    direct_link: str | None
    direction: str | None
    status: str | None
    missed_call_reason: str | None
    started_at: int | None
    answered_at: int | None
    ended_at: int | None
    duration: int | None
    voicemail: Any
    archived: bool | None
    cost: str | None
    number: AircallNumber
    user: AircallUser
    contact: AircallContact
    raw_digits: str | None
    asset: str | None
    recording: str | None
    transcription: AircallTranscription


@dataclass(frozen=True)
class SmartMovingBranch:
    id: str | None
    name: str | None


@dataclass(frozen=True)
class SmartMovingTariff:
    id: str | None
    name: str | None


@dataclass(frozen=True)
class SmartMovingCustomer:
    id: str | None
    first_name: str | None
    last_name: str | None
    phone_number: str | None
    email_address: str | None


@dataclass(frozen=True)
class SmartMovingSalesPerson:
    id: str | None
    name: str | None
    email: str | None


@dataclass(frozen=True)
class SmartMovingLeadSource:
    name: str | None


@dataclass(frozen=True)
class SmartMovingStop:
    order: int | None
    type: str | None
    address_full_address: str | None
    address_unit: str | None
    property_type: int | None
    property_type_name: str | None
    stairs: int | None
    has_elevator: bool | None
    parking_description: str | None
    notes: str | None


@dataclass(frozen=True)
class SmartMovingNotes:
    internal_notes: str | None
    customer_notes: str | None
    crew_notes: str | None
    crew_feedback: str | None
    dispatcher_notes: str | None
    accounting_notes: str | None


@dataclass(frozen=True)
class SmartMovingCharge:
    name: str | None
    rate: str | None
    subtotal: float | int | None
    discount: float | int | None
    total_cost: float | int | None


@dataclass(frozen=True)
class SmartMovingInventoryRoom:
    name: str | None
    item_count: int | None


@dataclass(frozen=True)
class SmartMovingInventoryItem:
    name: str | None
    quantity: int | None
    estimated_weight_lbs: int | None


@dataclass(frozen=True)
class SmartMovingInventory:
    total_volume_cu_ft: int | None
    total_weight_lbs: int | None
    rooms: list[SmartMovingInventoryRoom]
    items: list[SmartMovingInventoryItem]


@dataclass(frozen=True)
class SmartMovingJob:
    id: str | None
    job_number: str | None
    type: int | None
    type_name: str | None
    service_date: int | None
    confirmed: bool | None
    scheduled: bool | None
    arrival_window: str | None
    estimated_duration: str | None
    crew_size: int | None
    truck_count: int | None
    estimated_charges: float | int | None
    stops: list[SmartMovingStop]
    notes: SmartMovingNotes
    charges: list[SmartMovingCharge]
    inventory: SmartMovingInventory


@dataclass(frozen=True)
class SmartMovingData:
    id: str | None
    quote_number: int | None
    status: int | None
    status_name: str | None
    type: int | None
    type_name: str | None
    created_at: str | None
    updated_at: str | None
    service_date: int | None
    move_size: str | None
    move_size_id: str | None
    branch: SmartMovingBranch
    tariff: SmartMovingTariff
    customer: SmartMovingCustomer
    sales_person: SmartMovingSalesPerson
    lead_source: SmartMovingLeadSource
    tags: list[Any]
    estimated_total: float | int | None
    subtotal: float | int | None
    discount: float | int | None
    sales_tax: float | int | None
    jobs: list[SmartMovingJob]
