"""
formatter functions
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from mycves.config import logger
from mycves.errors import FormatException


def round_time(date: datetime) -> datetime:
    """
    round datetime to minutes
    """
    return date - timedelta(seconds=date.second, microseconds=date.microsecond)


def format_parameter_time(time: datetime) -> str:
    """
    format time according to the specified format in the api docs and normalize it to utc
    """
    return time.astimezone(timezone.utc).isoformat()
    formatted_time = time.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    return f"{formatted_time}:000 UTC+00:00"


def format_cpe_match(cpe: Optional[str]) -> Optional[str]:
    """
    format cpe match string
    """
    if cpe is not None:
        try:
            return " ".join(cpe.split(":")[3:6]).rstrip("-")
        except Exception as e:
            logger.exception(e)
            raise FormatException(f"Formatting CPE match failed for cpe {cpe}")
    return None


def format_cve_dates(cve_date: str) -> str:
    """
    format publish/modify date for cpe
    """
    try:
        return datetime.fromisoformat(cve_date).strftime("%Y-%m-%d")
        # return cve_date.split("T")[0]
    except Exception as e:
        logger.exception(e)
        raise FormatException(f"Formating Cve date failed for date {cve_date}")
