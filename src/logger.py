"""
basic logger configuration
"""

import logging
from pathlib import Path


def get_logger(file: Path):
    """create the package wide logger"""
    file_frm = logging.Formatter(
        "{asctime} {levelname}: {message}", "%d.%m.%Y %H:%M:%S", style="{"
    )
    stdout_frm = logging.Formatter("%(message)s")
    logger = logging.getLogger(__package__)
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(file)
    file_handler.setFormatter(file_frm)
    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(stdout_frm)
    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)
    logger.propagate = False
    return logger
