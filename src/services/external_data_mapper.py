from __future__ import annotations

import logging
from typing import Any

from src.models.external_data import (
    AircallContact,
    AircallData,
    AircallEmail,
    AircallNumber,
    AircallPhoneNumber,
    AircallTranscriptChannel,
    AircallTranscriptContent,
    AircallTranscription,
    AircallUser,
    AircallUtterance,
    SmartMovingBranch,
    SmartMovingCharge,
    SmartMovingCustomer,
    SmartMovingData,
    SmartMovingInventory,
    SmartMovingInventoryItem,
    SmartMovingInventoryRoom,
    SmartMovingJob,
    SmartMovingLeadSource,
    SmartMovingNotes,
    SmartMovingSalesPerson,
    SmartMovingStop,
    SmartMovingTariff,
)

logger = logging.getLogger("ExternalDataMapper")


class ExternalDataMapper:
    def map_aircall(self, data: dict[str, Any]) -> AircallData:
        logger.info("Mapping Aircall JSON to AircallData")

        number = self._as_dict(data.get("number"))
        user = self._as_dict(data.get("user"))
        contact = self._as_dict(data.get("contact"))
        transcription = self._as_dict(data.get("transcription"))
        content = self._as_dict(transcription.get("content"))

        return AircallData(
            id=data.get("id"),
            direct_link=data.get("direct_link"),
            direction=data.get("direction"),
            status=data.get("status"),
            missed_call_reason=data.get("missed_call_reason"),
            started_at=data.get("started_at"),
            answered_at=data.get("answered_at"),
            ended_at=data.get("ended_at"),
            duration=data.get("duration"),
            voicemail=data.get("voicemail"),
            archived=data.get("archived"),
            cost=data.get("cost"),
            number=AircallNumber(
                id=number.get("id"),
                name=number.get("name"),
                digits=number.get("digits"),
                country=number.get("country"),
            ),
            user=AircallUser(
                id=user.get("id"),
                name=user.get("name"),
                email=user.get("email"),
                available=user.get("available"),
            ),
            contact=AircallContact(
                id=contact.get("id"),
                first_name=contact.get("first_name"),
                last_name=contact.get("last_name"),
                company_name=contact.get("company_name"),
                phone_numbers=[
                    AircallPhoneNumber(
                        label=phone_number.get("label"),
                        value=phone_number.get("value"),
                    )
                    for phone_number in self._as_dict_list(contact.get("phone_numbers"))
                ],
                emails=[
                    AircallEmail(
                        label=email.get("label"),
                        value=email.get("value"),
                    )
                    for email in self._as_dict_list(contact.get("emails"))
                ],
            ),
            raw_digits=data.get("raw_digits"),
            asset=data.get("asset"),
            recording=data.get("recording"),
            transcription=AircallTranscription(
                id=transcription.get("id"),
                call_id=transcription.get("call_id"),
                language=transcription.get("language"),
                created_at=transcription.get("created_at"),
                content=AircallTranscriptContent(
                    channels=[
                        AircallTranscriptChannel(
                            speaker=channel.get("speaker"),
                            name=channel.get("name"),
                        )
                        for channel in self._as_dict_list(content.get("channels"))
                    ],
                    utterances=[
                        AircallUtterance(
                            start=utterance.get("start"),
                            end=utterance.get("end"),
                            speaker=utterance.get("speaker"),
                            text=utterance.get("text"),
                        )
                        for utterance in self._as_dict_list(content.get("utterances"))
                    ],
                ),
            ),
        )

    def map_smartmoving(self, data: dict[str, Any]) -> SmartMovingData:
        logger.info("Mapping SmartMoving JSON to SmartMovingData")

        branch = self._as_dict(data.get("branch"))
        tariff = self._as_dict(data.get("tariff"))
        customer = self._as_dict(data.get("customer"))
        sales_person = self._as_dict(data.get("salesPerson"))
        lead_source = self._as_dict(data.get("leadSource"))

        return SmartMovingData(
            id=data.get("id"),
            quote_number=data.get("quoteNumber"),
            status=data.get("status"),
            status_name=data.get("statusName"),
            type=data.get("type"),
            type_name=data.get("typeName"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            service_date=data.get("serviceDate"),
            move_size=data.get("moveSize"),
            move_size_id=data.get("moveSizeId"),
            branch=SmartMovingBranch(
                id=branch.get("id"),
                name=branch.get("name"),
            ),
            tariff=SmartMovingTariff(
                id=tariff.get("id"),
                name=tariff.get("name"),
            ),
            customer=SmartMovingCustomer(
                id=customer.get("id"),
                first_name=customer.get("firstName"),
                last_name=customer.get("lastName"),
                phone_number=customer.get("phoneNumber"),
                email_address=customer.get("emailAddress"),
            ),
            sales_person=SmartMovingSalesPerson(
                id=sales_person.get("id"),
                name=sales_person.get("name"),
                email=sales_person.get("email"),
            ),
            lead_source=SmartMovingLeadSource(
                name=lead_source.get("name"),
            ),
            tags=data.get("tags") if isinstance(data.get("tags"), list) else [],
            estimated_total=data.get("estimatedTotal"),
            subtotal=data.get("subtotal"),
            discount=data.get("discount"),
            sales_tax=data.get("salesTax"),
            jobs=[
                self._map_smartmoving_job(job)
                for job in self._as_dict_list(data.get("jobs"))
            ],
        )

    def _map_smartmoving_job(self, job: dict[str, Any]) -> SmartMovingJob:
        notes = self._as_dict(job.get("notes"))
        inventory = self._as_dict(job.get("inventory"))

        return SmartMovingJob(
            id=job.get("id"),
            job_number=job.get("jobNumber"),
            type=job.get("type"),
            type_name=job.get("typeName"),
            service_date=job.get("serviceDate"),
            confirmed=job.get("confirmed"),
            scheduled=job.get("scheduled"),
            arrival_window=job.get("arrivalWindow"),
            estimated_duration=job.get("estimatedDuration"),
            crew_size=job.get("crewSize"),
            truck_count=job.get("truckCount"),
            estimated_charges=job.get("estimatedCharges"),
            stops=[
                SmartMovingStop(
                    order=stop.get("order"),
                    type=stop.get("type"),
                    address_full_address=stop.get("addressFullAddress"),
                    address_unit=stop.get("addressUnit"),
                    property_type=stop.get("propertyType"),
                    property_type_name=stop.get("propertyTypeName"),
                    stairs=stop.get("stairs"),
                    has_elevator=stop.get("hasElevator"),
                    parking_description=stop.get("parkingDescription"),
                    notes=stop.get("notes"),
                )
                for stop in self._as_dict_list(job.get("stops"))
            ],
            notes=SmartMovingNotes(
                internal_notes=notes.get("internalNotes"),
                customer_notes=notes.get("customerNotes"),
                crew_notes=notes.get("crewNotes"),
                crew_feedback=notes.get("crewFeedback"),
                dispatcher_notes=notes.get("dispatcherNotes"),
                accounting_notes=notes.get("accountingNotes"),
            ),
            charges=[
                SmartMovingCharge(
                    name=charge.get("name"),
                    rate=charge.get("rate"),
                    subtotal=charge.get("subtotal"),
                    discount=charge.get("discount"),
                    total_cost=charge.get("totalCost"),
                )
                for charge in self._as_dict_list(job.get("charges"))
            ],
            inventory=SmartMovingInventory(
                total_volume_cu_ft=inventory.get("totalVolumeCuFt"),
                total_weight_lbs=inventory.get("totalWeightLbs"),
                rooms=[
                    SmartMovingInventoryRoom(
                        name=room.get("name"),
                        item_count=room.get("itemCount"),
                    )
                    for room in self._as_dict_list(inventory.get("rooms"))
                ],
                items=[
                    SmartMovingInventoryItem(
                        name=item.get("name"),
                        quantity=item.get("quantity"),
                        estimated_weight_lbs=item.get("estimatedWeightLbs"),
                    )
                    for item in self._as_dict_list(inventory.get("items"))
                ],
            ),
        )

    @staticmethod
    def _as_dict(value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _as_dict_list(value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []

        return [item for item in value if isinstance(item, dict)]
