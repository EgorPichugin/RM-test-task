from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("PathValidator")


@dataclass(frozen=True)
class FilePathValidationResult:
    base_path: Path
    resolved_files: list[Path]


class FilePathValidationError(Exception):
    pass


class FilePathValidator:
    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path

    def validate(self, input_files: list[Path]) -> FilePathValidationResult:
        base_path = self.base_path
        self._validate_base_path(base_path)

        resolved_files = [
            self._resolve_input_file(base_path, input_file)
            for input_file in input_files
        ]
        missing_files = [
            file_path
            for file_path in resolved_files
            if not self._is_file(file_path)
        ]

        for file_path in resolved_files:
            if file_path in missing_files:
                logger.warning('File not found: "%s"', file_path)
            else:
                logger.info('File found: "%s"', file_path)

        if missing_files:
            raise FilePathValidationError(
                f'File or files are not found in the provided path "{base_path}"'
            )

        return FilePathValidationResult(
            base_path=base_path,
            resolved_files=resolved_files,
        )

    def _validate_base_path(self, base_path: Path) -> None:
        if not self._is_directory(base_path):
            logger.error('Folder does not exist: "%s"', base_path)
            raise FilePathValidationError(
                f'Provided path "{base_path}" is not a valid directory'
            )

        logger.info('Folder exists: "%s"', base_path)

    def _resolve_input_file(self, base_path: Path, input_file: Path) -> Path:
        if input_file.is_absolute():
            resolved_file = self._normalize_path(str(input_file))
            logger.info('Resolved absolute input file "%s" to "%s"', input_file, resolved_file)
            return resolved_file

        resolved_file = self._normalize_path(str(base_path / input_file))
        logger.info('Resolved input file "%s" to "%s"', input_file, resolved_file)
        return resolved_file

    @staticmethod
    def _normalize_path(raw_path: str) -> Path:
        path = Path(raw_path.strip()).expanduser()
        return path.resolve(strict=False)

    @staticmethod
    def _is_directory(path: Path) -> bool:
        try:
            return path.is_dir()
        except OSError:
            return False

    @staticmethod
    def _is_file(path: Path) -> bool:
        try:
            return path.is_file()
        except OSError:
            return False
