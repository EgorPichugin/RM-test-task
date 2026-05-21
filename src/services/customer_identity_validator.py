from __future__ import annotations

import logging
import re

from src.models.external_data import AircallData, SmartMovingData

logger = logging.getLogger("CustomerIdentityValidator")


class CustomerIdentityValidationError(Exception):
    pass


class CustomerIdentityValidator:
    def validate(
        self,
        aircall_data: AircallData,
        smartmoving_data: SmartMovingData,
    ) -> None:
        aircall_phone = self._extract_aircall_phone(aircall_data)
        smartmoving_phone = smartmoving_data.customer.phone_number
        aircall_email = self._extract_aircall_email(aircall_data)
        smartmoving_email = smartmoving_data.customer.email_address
        aircall_full_name = self._build_full_name(
            aircall_data.contact.first_name,
            aircall_data.contact.last_name,
        )
        smartmoving_full_name = self._build_full_name(
            smartmoving_data.customer.first_name,
            smartmoving_data.customer.last_name,
        )

        logger.info(
            'Validating customer identity. Aircall name="%s", SmartMoving name="%s"',
            aircall_full_name,
            smartmoving_full_name,
        )

        if self._phones_match(aircall_phone, smartmoving_phone):
            logger.info("Customer identity matched by phone number")
            return

        if self._emails_match(aircall_email, smartmoving_email):
            logger.info("Customer identity matched by email address")
            return

        if self._names_match(aircall_full_name, smartmoving_full_name):
            logger.warning("Customer identity matched only by first and last name")
            return

        logger.error(
            "Customer identity does not match. "
            'Aircall phone="%s", SmartMoving phone="%s", '
            'Aircall email="%s", SmartMoving email="%s", '
            'Aircall name="%s", SmartMoving name="%s"',
            aircall_phone,
            smartmoving_phone,
            aircall_email,
            smartmoving_email,
            aircall_full_name,
            smartmoving_full_name,
        )
        raise CustomerIdentityValidationError(
            "Customer identity does not match between Aircall and SmartMoving data"
        )

    @staticmethod
    def _extract_aircall_phone(aircall_data: AircallData) -> str | None:
        for phone_number in aircall_data.contact.phone_numbers:
            if phone_number.value:
                return phone_number.value

        return aircall_data.raw_digits

    @staticmethod
    def _extract_aircall_email(aircall_data: AircallData) -> str | None:
        for email in aircall_data.contact.emails:
            if email.value:
                return email.value

        return None

    def _phones_match(
        self,
        aircall_phone: str | None,
        smartmoving_phone: str | None,
    ) -> bool:
        normalized_aircall_phone = self._normalize_phone(aircall_phone)
        normalized_smartmoving_phone = self._normalize_phone(smartmoving_phone)

        if not normalized_aircall_phone or not normalized_smartmoving_phone:
            logger.info("Phone number comparison skipped because one value is missing")
            return False

        return normalized_aircall_phone == normalized_smartmoving_phone

    def _emails_match(
        self,
        aircall_email: str | None,
        smartmoving_email: str | None,
    ) -> bool:
        normalized_aircall_email = self._normalize_email(aircall_email)
        normalized_smartmoving_email = self._normalize_email(smartmoving_email)

        if not normalized_aircall_email or not normalized_smartmoving_email:
            logger.info("Email comparison skipped because one value is missing")
            return False

        return normalized_aircall_email == normalized_smartmoving_email

    def _names_match(
        self,
        aircall_full_name: str,
        smartmoving_full_name: str,
    ) -> bool:
        normalized_aircall_name = self._normalize_name(aircall_full_name)
        normalized_smartmoving_name = self._normalize_name(smartmoving_full_name)

        if not normalized_aircall_name or not normalized_smartmoving_name:
            logger.info("Name comparison skipped because one value is missing")
            return False

        return normalized_aircall_name == normalized_smartmoving_name

    @staticmethod
    def _build_full_name(first_name: str | None, last_name: str | None) -> str:
        return " ".join(
            name_part.strip()
            for name_part in (first_name, last_name)
            if name_part and name_part.strip()
        )

    @staticmethod
    def _normalize_phone(phone_number: str | None) -> str:
        if phone_number is None:
            return ""

        phone_digits = re.sub(r"\D", "", phone_number)
        if len(phone_digits) >= 10:
            return phone_digits[-10:]

        return phone_digits

    @staticmethod
    def _normalize_name(name: str | None) -> str:
        if name is None:
            return ""

        normalized_name = name.casefold().strip()
        return re.sub(r"\s+", " ", normalized_name)

    @staticmethod
    def _normalize_email(email: str | None) -> str:
        if email is None:
            return ""

        return email.casefold().strip()
