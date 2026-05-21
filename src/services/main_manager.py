from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.services.context_extractor import ContextExtractor, ExtractedContext
from src.services.customer_identity_validator import CustomerIdentityValidator
from src.services.file_path_validator import FilePathValidationResult, FilePathValidator
from src.services.object_structure_validator import ObjectStructureValidationResult, ObjectStructureValidator
from src.services.precheck_service import PreCheckResult, PreCheckService


@dataclass(frozen=True)
class MainManagerResult:
    input_files: list[Path]
    aircall_file: Path
    smartmoving_file: Path
    llm_context: dict[str, Any]
    findings: list[dict[str, str]]
    precheck: dict[str, Any]
    warning_message: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "input_files": [str(path) for path in self.input_files],
            "aircall_file": str(self.aircall_file),
            "smartmoving_file": str(self.smartmoving_file),
            "llm_context": self.llm_context,
            "precheck": self.precheck,
            "warning_message": self.warning_message,
            "findings": self.findings,
        }


class MainManagerService:
    def __init__(
        self,
        file_path_validator: FilePathValidator,
        object_structure_validator: ObjectStructureValidator,
        customer_identity_validator: CustomerIdentityValidator,
        context_extractor: ContextExtractor,
        precheck_service: PreCheckService,
    ) -> None:
        self.file_path_validator = file_path_validator
        self.object_structure_validator = object_structure_validator
        self.customer_identity_validator = customer_identity_validator
        self.context_extractor = context_extractor
        self.precheck_service = precheck_service

    def run(self, input_files: list[Path]) -> MainManagerResult:
        # check file paths and resolve them
        file_path_result: FilePathValidationResult = self.file_path_validator.validate(input_files)

        # check files structure aircall or smartmoving
        object_structure_result: ObjectStructureValidationResult = self.object_structure_validator.validate(
            file_path_result.resolved_files,
        )

        # check that Aircall contact and SmartMoving customer are the same person
        self.customer_identity_validator.validate(
            aircall_data=object_structure_result.aircall_data,
            smartmoving_data=object_structure_result.smartmoving_data,
        )

        # extract context for LLM
        extracted_context: ExtractedContext = self.context_extractor.extract(
            aircall_data=object_structure_result.aircall_data,
            smartmoving_data=object_structure_result.smartmoving_data,
        )

        precheck_result: PreCheckResult = self.precheck_service.check(extracted_context)
        if precheck_result.should_return_empty_findings:
            return MainManagerResult(
                input_files=file_path_result.resolved_files,
                aircall_file=object_structure_result.aircall_file,
                smartmoving_file=object_structure_result.smartmoving_file,
                llm_context=extracted_context.to_dict(),
                findings=[],
                precheck=precheck_result.to_dict(),
                warning_message=precheck_result.warning_message,
            )

        return MainManagerResult(
            input_files=file_path_result.resolved_files,
            aircall_file=object_structure_result.aircall_file,
            smartmoving_file=object_structure_result.smartmoving_file,
            llm_context=extracted_context.to_dict(),
            findings=[],
            precheck=precheck_result.to_dict(),
        )
