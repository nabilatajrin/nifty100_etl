"""Normalisation helpers for the NIFTY 100 ETL pipeline (Sprint 1, Day 2)."""

import re

PARSE_ERROR = "PARSE_ERROR"

# Month name/abbreviation -> two-digit month
_MONTHS = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "may": "05", "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
    "january": "01", "february": "02", "march": "03", "april": "04",
    "june": "06", "july": "07", "august": "08", "september": "09",
    "october": "10", "november": "11", "december": "12",
}


def normalize_year(raw) -> str:
    """Standardise a financial-year label to 'YYYY-MM', else 'PARSE_ERROR'."""
    if raw is None:
        return PARSE_ERROR
    s = str(raw).strip()
    if not s:
        return PARSE_ERROR

    # Already normalised: 2023-03
    m = re.fullmatch(r"(\d{4})-(\d{2})", s)
    if m and 1 <= int(m.group(2)) <= 12:
        return s

    # Plain 4-digit year -> assume March FY close
    if re.fullmatch(r"\d{4}", s):
        return f"{s}-03"

    # FY prefix: FY23, FY2023, FY 24
    m = re.fullmatch(r"FY\s*(\d{2,4})", s, re.IGNORECASE)
    if m:
        yr = m.group(1)
        if len(yr) == 2:
            yr = "20" + yr
        return f"{yr}-03"

    # Month-Year: Mar-23, Mar 23, March-2023, Dec-22, Jun-23
    m = re.fullmatch(r"([A-Za-z]+)[\s\-]+(\d{2,4})", s)
    if m:
        mon = m.group(1).lower()
        yr = m.group(2)
        if mon in _MONTHS:
            if len(yr) == 2:
                yr = "20" + yr
            return f"{yr}-{_MONTHS[mon]}"

    # Year-Month worded the other way: 2023-Mar
    m = re.fullmatch(r"(\d{4})[\s\-]+([A-Za-z]+)", s)
    if m:
        yr = m.group(1)
        mon = m.group(2).lower()
        if mon in _MONTHS:
            return f"{yr}-{_MONTHS[mon]}"

    return PARSE_ERROR


def normalize_ticker(raw) -> str:
    """Strip whitespace and upper-case a ticker. Empty/None -> '' (reject upstream)."""
    if raw is None:
        return ""
    return str(raw).strip().upper()
