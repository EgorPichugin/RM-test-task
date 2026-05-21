from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

from src.config.settings import (
    ANTHROPIC_KEY_ENV_KEY,
    DEFAULT_FILES_PATH,
    DEFAULT_MODEL,
    ENV_FILE_PATH,
    FILES_PATH_ENV_KEY,
    MODEL_ENV_KEY,
)

logger = logging.getLogger("EnvValidator")


class EnvValidationError(Exception):
    pass


@dataclass(frozen=True)
class EnvValidationResult:
    files_path: Path
    anthropic_key: str
    model: str


class EnvValidator:
    REQUIRED_ENV_KEYS = (
        ANTHROPIC_KEY_ENV_KEY,
    )

    def __init__(self, env_path: Path = ENV_FILE_PATH) -> None:
        self.env_path = env_path

    def validate(self) -> EnvValidationResult:
        logger.info("Validating environment values")

        env_values = self._load_env_values()

        missing_keys = [
            env_key
            for env_key in self.REQUIRED_ENV_KEYS
            if not self._has_value(env_values.get(env_key))
        ]

        if missing_keys:
            logger.error(
                "Missing required environment value(s): %s",
                ", ".join(missing_keys),
            )
            raise EnvValidationError(
                "Missing required environment value(s): "
                f"{', '.join(missing_keys)}"
            )

        files_path = self._resolve_files_path(env_values.get(FILES_PATH_ENV_KEY))
        anthropic_key = str(env_values[ANTHROPIC_KEY_ENV_KEY]).strip()
        model = self._resolve_model(env_values.get(MODEL_ENV_KEY))
        os.environ[FILES_PATH_ENV_KEY] = str(files_path)
        os.environ[ANTHROPIC_KEY_ENV_KEY] = anthropic_key
        os.environ[MODEL_ENV_KEY] = model

        logger.info('Configured files path: "%s"', files_path)
        logger.info('Configured model: "%s"', model)
        logger.info("Environment validation completed successfully")
        return EnvValidationResult(
            files_path=files_path,
            anthropic_key=anthropic_key,
            model=model,
        )

    def _load_env_values(self) -> dict[str, str | None]:
        if self.env_path.is_file():
            logger.info('Loading environment values from "%s"', self.env_path)
            env_values = dict(dotenv_values(self.env_path))
        else:
            logger.info(
                'Environment file "%s" was not found. Using process environment.',
                self.env_path,
            )
            env_values = {}

        for env_key in (
            FILES_PATH_ENV_KEY,
            ANTHROPIC_KEY_ENV_KEY,
            MODEL_ENV_KEY,
        ):
            if env_key in os.environ:
                env_values[env_key] = os.environ[env_key]

        return env_values

    def _resolve_files_path(self, value: object) -> Path:
        if self._has_value(value):
            return self._normalize_path(str(value))

        default_files_path = DEFAULT_FILES_PATH.resolve(strict=False)
        logger.warning(
            'Environment value "%s" is missing or empty. Using default files path "%s"',
            FILES_PATH_ENV_KEY,
            default_files_path,
        )
        return default_files_path

    def _resolve_model(self, value: object) -> str:
        if self._has_value(value):
            return str(value).strip()

        logger.warning(
            'Environment value "%s" is missing or empty. Using default model "%s"',
            MODEL_ENV_KEY,
            DEFAULT_MODEL,
        )
        return DEFAULT_MODEL

    @staticmethod
    def _has_value(value: object) -> bool:
        return isinstance(value, str) and bool(value.strip())

    @staticmethod
    def _normalize_path(raw_path: str) -> Path:
        path = Path(raw_path.strip()).expanduser()
        return path.resolve(strict=False)
