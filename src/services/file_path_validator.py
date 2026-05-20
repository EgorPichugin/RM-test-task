from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from src.config.settings import ENV_FILE_PATH, FILES_PATH_ENV_KEY

logger = logging.getLogger("PathValidator")


@dataclass(frozen=True)
class FilePathValidationResult:
    base_path: Path
    resolved_files: list[Path]


class FilePathValidationError(Exception):
    pass


class FilePathValidator:
    def __init__(
        self,
        env_path: Path = ENV_FILE_PATH,
        env_key: str = FILES_PATH_ENV_KEY,
    ) -> None:
        self.env_path = env_path
        self.env_key = env_key

    def validate(self, input_files: list[Path]) -> FilePathValidationResult:
        base_path = self._read_base_path()
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

    def _read_base_path(self) -> Path:
        if not self.env_path.is_file():
            logger.error('Environment file not found: "%s"', self.env_path)
            raise FilePathValidationError(
                f'File or files are not found in the provided path "{self.env_path}"'
            )

        logger.info('Loading environment file: "%s"', self.env_path)
        load_dotenv(self.env_path)
        raw_base_path = os.getenv(self.env_key, "")
        base_path = self._normalize_path(raw_base_path)
        logger.info('Configured files path: "%s"', base_path)
        return base_path

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
