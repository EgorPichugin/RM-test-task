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
        aircall_first_name = aircall_data.contact.first_name
        aircall_last_name = aircall_data.contact.last_name
        smartmoving_first_name = smartmoving_data.customer.first_name
        smartmoving_last_name = smartmoving_data.customer.last_name

        logger.info(
            'Validating customer identity. Aircall="%s %s", SmartMoving="%s %s"',
            aircall_first_name,
            aircall_last_name,
            smartmoving_first_name,
            smartmoving_last_name,
        )

        if not self._has_required_names(
            aircall_first_name,
            aircall_last_name,
            smartmoving_first_name,
            smartmoving_last_name,
        ):
            logger.error("Customer first name or last name is missing")
            raise CustomerIdentityValidationError(
                "Customer first name or last name is missing in Aircall or SmartMoving data"
            )

        if self._normalize_name(aircall_first_name) != self._normalize_name(smartmoving_first_name):
            logger.error(
                'Customer first names do not match. Aircall="%s", SmartMoving="%s"',
                aircall_first_name,
                smartmoving_first_name,
            )
            raise CustomerIdentityValidationError(
                "Customer first name does not match between Aircall and SmartMoving data"
            )

        if self._normalize_name(aircall_last_name) != self._normalize_name(smartmoving_last_name):
            logger.error(
                'Customer last names do not match. Aircall="%s", SmartMoving="%s"',
                aircall_last_name,
                smartmoving_last_name,
            )
            raise CustomerIdentityValidationError(
                "Customer last name does not match between Aircall and SmartMoving data"
            )

        logger.info("Customer identity validation completed successfully")

    @staticmethod
    def _has_required_names(*names: str | None) -> bool:
        return all(name is not None and name.strip() for name in names)

    @staticmethod
    def _normalize_name(name: str | None) -> str:
        if name is None:
            return ""

        normalized_name = name.casefold().strip()
        return re.sub(r"\s+", " ", normalized_name)
