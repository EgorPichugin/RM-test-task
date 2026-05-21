from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("JsonOutputWriter")


class JsonOutputWriterError(Exception):
    pass


class JsonOutputWriter:
    OUTPUT_FOLDER_NAME = "outputs"

    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path

    def write(self, file_name: str, data: dict[str, Any]) -> Path:
        return self.write_json_output(
            file_name=file_name,
            json_output=json.dumps(data, indent=2, ensure_ascii=False),
        )

    def write_json_output(self, file_name: str, json_output: str) -> Path:
        output_dir = self.base_path / self.OUTPUT_FOLDER_NAME
        output_path = output_dir / file_name

        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json_output,
                encoding="utf-8",
            )
        except OSError as error:
            logger.error('Failed to write JSON output to "%s": %s', output_path, error)
            raise JsonOutputWriterError(
                f'Failed to write JSON output to "{output_path}"'
            ) from error

        logger.info('JSON output written to "%s"', output_path)
        return output_path
