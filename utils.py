"""
This module provides helper functions
"""

from typing import Tuple
from datetime import datetime, timedelta, date
from queue import Queue


def get_date(
    from_date_str: str,
    to_date_str: str,
    forward_period: int,
    look_back: int,
) -> Tuple[date, date, date, date]:
    """
        Return required dates from backtesting period str

    Args:
        from_date_str (str)
        to_date_str (str)
        forward_period (int)
        look_back (int)

    Returns:
        Tuple[ datetime.date, datetime.date, datetime.date, datetime.date ]
    """

    from_date = datetime.strptime(from_date_str, "%Y-%m-%d")
    to_date = datetime.strptime(to_date_str, "%Y-%m-%d")
    forward_delta = timedelta(days=forward_period)
    look_back_delta = timedelta(days=look_back)

    start = from_date - look_back_delta
    end = to_date + forward_delta
    return start.date(), from_date.date(), to_date.date(), end.date()


def first_date_of_months(start_date_str: str, end_date_str: str) -> Queue:
    """
    Get list of first dates of months

    Args:
        start_date_str (str)
        end_date_str (str)

    Returns:
        Queue
    """
    first_days = Queue()

    current_date = datetime.strptime(start_date_str, "%Y-%m-%d").replace(day=1)
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    while current_date <= end_date:
        first_days.put(current_date.date())
        month = current_date.month % 12 + 1
        next_month = (
            current_date.replace(year=current_date.year + 1, month=month, day=1)
            if month == 1
            else current_date.replace(month=month, day=1)
        )

        current_date = next_month

    return first_days


def round_lot(quantity: int) -> int:
    """
    Rounding quantity to trading lot

    Args:
        quantity (int)
    Returns:
        int
    """
    return int(quantity // 100) * 100
