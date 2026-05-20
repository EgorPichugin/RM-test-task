from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.services.file_path_validator import FilePathValidator
from src.services.object_structure_validator import ObjectStructureValidator


@dataclass(frozen=True)
class MainManagerResult:
    input_files: list[Path]
    aircall_file: Path
    smartmoving_file: Path
    findings: list[dict[str, str]]

    def to_dict(self) -> dict[str, object]:
        return {
            "input_files": [str(path) for path in self.input_files],
            "aircall_file": str(self.aircall_file),
            "smartmoving_file": str(self.smartmoving_file),
            "findings": self.findings,
        }


class MainManagerService:
    def __init__(
        self,
        file_path_validator: FilePathValidator,
        object_structure_validator: ObjectStructureValidator,
    ) -> None:
        self.file_path_validator = file_path_validator
        self.object_structure_validator = object_structure_validator

    def run(self, input_files: list[Path]) -> MainManagerResult:
        file_path_result = self.file_path_validator.validate(input_files)
        object_structure_result = self.object_structure_validator.validate(
            file_path_result.resolved_files,
        )

        return MainManagerResult(
            input_files=file_path_result.resolved_files,
            aircall_file=object_structure_result.aircall_file,
            smartmoving_file=object_structure_result.smartmoving_file,
            findings=[],
        )
