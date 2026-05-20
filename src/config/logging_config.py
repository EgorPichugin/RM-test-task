from __future__ import annotations

import logging


class ColorFormatter(logging.Formatter):
    RESET = "\033[0m"
    COLORS = {
        logging.DEBUG: "\033[36m",
        logging.INFO: "\033[32m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[35m",
    }

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        color = self.COLORS.get(record.levelno, self.RESET)
        return f"{color}{message}{self.RESET}"


def setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(
        ColorFormatter("%(levelname)s:%(name)s:%(message)s")
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
