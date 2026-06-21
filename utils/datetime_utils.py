# utils/datetime_util.py   ← ফাইল নাম রাখো এটা
from __future__ import annotations

import re
from datetime import datetime, date
from functools import lru_cache
from typing import Union, Any, Optional

__all__ = ["DateTimeUtil"]


class DateTimeUtil:
    _ORACLE_RE = re.compile(r"^(\d{1,2})[-/](\w+)[-/](\d{2,4})$", re.I)
    _HAS_TIME_RE = re.compile(r"[ T:]")

    _BANGLA_MONTHS = {
        "জানু": "Jan", "জান": "Jan", "জানুয়ারি": "Jan",
        "ফেব্রু": "Feb", "ফেব": "Feb", "ফেব্রুয়ারি": "Feb",
        "মার্চ": "Mar", "এপ্রি": "Apr", "এপ্রিল": "Apr",
        "মে": "May", "জুন": "Jun", "জুলা": "Jul", "জুলাই": "Jul",
        "আগস্ট": "Aug", "সেপ্টে": "Sep", "সেপ্টেম্বর": "Sep",
        "অক্টো": "Oct", "অক্টোবর": "Oct",
        "নভে": "Nov", "নভেম্বর": "Nov",
        "ডিসে": "Dec", "ডিসেম্বর": "Dec",
    }

    @staticmethod
    @lru_cache(maxsize=2048)
    def _fix_month(m: str) -> str:
        m = m.strip().title()
        for b, e in DateTimeUtil._BANGLA_MONTHS.items():
            if b in m:
                return e
        return m[:3]

    @staticmethod
    def parse(value: Any) -> Optional[Union[datetime, date]]:
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if not isinstance(value, str):
            return None

        s = value.strip()
        if not s:
            return None

        if DateTimeUtil._HAS_TIME_RE.search(s):
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y/%m/%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S.%f",
            ]
            for fmt in formats:
                try:
                    length = 26 if "." in s else 19
                    return datetime.strptime(s[:length], fmt)
                except ValueError:
                    pass

        date_formats = [
            "%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y",
            "%Y.%m.%d", "%d.%m.%Y", "%Y%m%d"
        ]
        for fmt in date_formats:
            try:
                return datetime.strptime(s[:10], fmt).date()
            except ValueError:
                pass

        # Oracle format: 04-Nov-25
        m = DateTimeUtil._ORACLE_RE.match(s.replace(" ", "-"))
        if m:
            d, mon, y = m.groups()
            mon = DateTimeUtil._fix_month(mon)
            y = int(y)
            y = y + 2000 if y < 50 else y + 1900 if y < 100 else y
            try:
                return datetime.strptime(f"{d}-{mon}-{y}", "%d-%b-%Y").date()
            except:
                pass

        return None

    @staticmethod
    def iso(value: Any) -> Union[datetime, date, None]:
        return DateTimeUtil.parse(value)
    
    @staticmethod
    def to_date(value: Any) -> Optional[date]:
        parsed = DateTimeUtil.parse(value)
        if parsed is None:
            return None
        return parsed.date() if isinstance(parsed, datetime) else parsed

    @staticmethod
    def format(value: Any, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        parsed = DateTimeUtil.parse(value)
        return parsed.strftime(fmt) if parsed else ""

    @staticmethod
    def display(value: Any) -> str:
        parsed = DateTimeUtil.parse(value)
        if not parsed:
            return ""
        if isinstance(parsed, datetime):
            return parsed.strftime("%d %b %Y, %H:%M:%S")
        return parsed.strftime("%d %b %Y")

    @staticmethod
    def expiry(value: Any) -> str:
        return DateTimeUtil.format(value, "%b %Y").upper()