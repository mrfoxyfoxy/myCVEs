"""
formatter functions
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from config import logger
from errors import FormatException


def round_time(date: datetime) -> datetime:
    """
    round datetime to minutes
    """
    return date - timedelta(seconds=date.second, microseconds=date.microsecond)


def format_parameter_time(time: datetime) -> str:
    """
    format time according to the specified format in the api docs and normalize it to utc  
    """        
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


def format_cpe_dates(cpe_date: Optional[str]) -> Optional[str]:
    """
    format publish/modify date for cpe
    """
    if cpe_date is not None:
        try:
            return cpe_date.split("T")[0]
        except Exception as e:
            logger.exception(e)
            raise FormatException(f"Formating CPE date failed for date {cpe_date}")
    return None
