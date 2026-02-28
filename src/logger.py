# -*- coding: utf-8 -*-
import logging
from typing import Optional


def setup_logger(name: str = "fanza_payload", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    return logger
