from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger("ObjectStructureValidator")


class ObjectStructureValidationError(Exception):
    pass


class ObjectType(str, Enum):
    AIRCALL = "aircall"
    SMARTMOVING = "smartmoving"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ObjectStructureValidationResult:
    aircall_file: Path
    smartmoving_file: Path
    aircall_data: dict[str, Any]
    smartmoving_data: dict[str, Any]


class ObjectStructureValidator:
    def validate(self, input_files: list[Path]) -> ObjectStructureValidationResult:
        logger.info("Validating object structures for %s file(s)", len(input_files))

        detected_objects = [
            self._detect_file_structure(file_path)
            for file_path in input_files
        ]

        aircall_matches = [
            detected
            for detected in detected_objects
            if detected.object_type == ObjectType.AIRCALL
        ]
        smartmoving_matches = [
            detected
            for detected in detected_objects
            if detected.object_type == ObjectType.SMARTMOVING
        ]
        invalid_matches = [
            detected
            for detected in detected_objects
            if detected.object_type == ObjectType.UNKNOWN
        ]

        if invalid_matches:
            invalid_files = ", ".join(str(detected.file_path) for detected in invalid_matches)
            logger.error("File structure is not recognized for: %s", invalid_files)
            raise ObjectStructureValidationError(
                f"File structure is not recognized for: {invalid_files}"
            )

        if len(aircall_matches) != 1 or len(smartmoving_matches) != 1:
            logger.error(
                "Invalid object mix. Aircall objects found: %s. SmartMoving objects found: %s.",
                len(aircall_matches),
                len(smartmoving_matches),
            )
            raise ObjectStructureValidationError(
                "Provided files must include exactly one Aircall object and "
                "exactly one SmartMoving object"
            )

        logger.info('Aircall object found: "%s"', aircall_matches[0].file_path)
        logger.info('SmartMoving object found: "%s"', smartmoving_matches[0].file_path)
        logger.info("Object structure validation completed successfully")

        return ObjectStructureValidationResult(
            aircall_file=aircall_matches[0].file_path,
            smartmoving_file=smartmoving_matches[0].file_path,
            aircall_data=aircall_matches[0].data,
            smartmoving_data=smartmoving_matches[0].data,
        )

    def _detect_file_structure(self, file_path: Path) -> "_DetectedObject":
        logger.info('Detecting object structure in "%s"', file_path)
        data = self._load_json(file_path)

        if self._is_aircall_object(data):
            logger.info('Detected Aircall structure in "%s"', file_path)
            return _DetectedObject(file_path, ObjectType.AIRCALL, data)

        if self._is_smartmoving_object(data):
            logger.info('Detected SmartMoving structure in "%s"', file_path)
            return _DetectedObject(file_path, ObjectType.SMARTMOVING, data)

        logger.warning('Unknown object structure in "%s"', file_path)
        logger.debug('Top-level keys in "%s": %s', file_path, sorted(data.keys()))
        return _DetectedObject(file_path, ObjectType.UNKNOWN, data)

    @staticmethod
    def _load_json(file_path: Path) -> dict[str, Any]:
        logger.info('Loading JSON file: "%s"', file_path)

        try:
            with file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            logger.error('Invalid JSON file "%s": %s', file_path, error)
            raise ObjectStructureValidationError(
                f'File "{file_path}" is not a valid JSON file'
            ) from error
        except OSError as error:
            logger.error('Unable to read JSON file "%s": %s', file_path, error)
            raise ObjectStructureValidationError(
                f'File "{file_path}" cannot be read'
            ) from error

        if not isinstance(data, dict):
            logger.error(
                'Invalid JSON root in "%s". Expected object, got %s',
                file_path,
                type(data).__name__,
            )
            raise ObjectStructureValidationError(
                f'File "{file_path}" must contain a JSON object'
            )

        logger.info('JSON file loaded successfully: "%s"', file_path)
        return data

    def _is_aircall_object(self, data: dict[str, Any]) -> bool:
        return all(
            [
                isinstance(data.get("id"), int),
                isinstance(data.get("direction"), str),
                isinstance(data.get("duration"), int),
                isinstance(data.get("contact"), dict),
                isinstance(data.get("user"), dict),
                self._has_nested_dict(data, ["transcription", "content"]),
                self._has_list(data, ["transcription", "content", "utterances"]),
                self._has_aircall_utterance_shape(data),
            ]
        )

    def _is_smartmoving_object(self, data: dict[str, Any]) -> bool:
        return all(
            [
                isinstance(data.get("id"), str),
                isinstance(data.get("quoteNumber"), int),
                isinstance(data.get("customer"), dict),
                isinstance(data.get("salesPerson"), dict),
                isinstance(data.get("jobs"), list),
                self._has_smartmoving_job_shape(data),
            ]
        )

    def _has_aircall_utterance_shape(self, data: dict[str, Any]) -> bool:
        utterances = self._get_nested_value(
            data,
            ["transcription", "content", "utterances"],
        )
        if not isinstance(utterances, list):
            return False

        return all(
            isinstance(utterance, dict)
            and isinstance(utterance.get("speaker"), str)
            and isinstance(utterance.get("text"), str)
            for utterance in utterances
        )

    def _has_smartmoving_job_shape(self, data: dict[str, Any]) -> bool:
        jobs = data.get("jobs")
        if not isinstance(jobs, list) or not jobs:
            return False

        return all(
            isinstance(job, dict)
            and isinstance(job.get("stops"), list)
            and isinstance(job.get("notes"), dict)
            and isinstance(job.get("charges"), list)
            and isinstance(job.get("inventory"), dict)
            and isinstance(job["inventory"].get("items"), list)
            for job in jobs
        )

    def _has_nested_dict(self, data: dict[str, Any], path: list[str]) -> bool:
        return isinstance(self._get_nested_value(data, path), dict)

    def _has_list(self, data: dict[str, Any], path: list[str]) -> bool:
        return isinstance(self._get_nested_value(data, path), list)

    @staticmethod
    def _get_nested_value(data: dict[str, Any], path: list[str]) -> Any:
        current_value: Any = data

        for key in path:
            if not isinstance(current_value, dict) or key not in current_value:
                return None
            current_value = current_value[key]

        return current_value


@dataclass(frozen=True)
class _DetectedObject:
    file_path: Path
    object_type: ObjectType
    data: dict[str, Any]
