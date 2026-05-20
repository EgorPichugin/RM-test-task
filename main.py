from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from src.config.logging_config import setup_logging
from src.services.file_path_validator import FilePathValidationError, FilePathValidator
from src.services.main_manager import MainManagerService
from src.services.object_structure_validator import (
    ObjectStructureValidationError,
    ObjectStructureValidator,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Find items mentioned in an Aircall transcript but missing from SmartMoving CRM data.",
    )
    parser.add_argument(
        "input_files",
        nargs=2,
        type=Path,
        metavar=("AIRCALL_JSON", "SMARTMOVING_JSON"),
        help="Paths to the Aircall and SmartMoving JSON files, in any order.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the JSON output.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    setup_logging()

    parser = build_parser()
    args = parser.parse_args(argv)

    manager = MainManagerService(
        file_path_validator=FilePathValidator(),
        object_structure_validator=ObjectStructureValidator(),
    )

    try:
        result = manager.run(args.input_files)
    except (FilePathValidationError, ObjectStructureValidationError) as error:
        print(str(error), file=sys.stderr)
        return 1

    indent = 2 if args.pretty else None
    print(
        json.dumps(
            result.to_dict(),
            indent=indent,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
