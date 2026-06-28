"""CAGR engine for the NIFTY 100 ratio engine (Sprint 2, Day 10).

CAGR = ((end / start) ** (1/n) - 1) * 100

Edge cases (per spec) return None plus a flag:
  Positive -> Positive : computed normally (flag None)
  Positive -> Negative : None, flag 'DECLINE_TO_LOSS'
  Negative -> Positive : None, flag 'TURNAROUND'
  Negative -> Negative : None, flag 'BOTH_NEGATIVE'
  Zero base            : None, flag 'ZERO_BASE'
  < n years of data    : None, flag 'INSUFFICIENT'
"""

NORMAL = None
DECLINE_TO_LOSS = "DECLINE_TO_LOSS"
TURNAROUND = "TURNAROUND"
BOTH_NEGATIVE = "BOTH_NEGATIVE"
ZERO_BASE = "ZERO_BASE"
INSUFFICIENT = "INSUFFICIENT"


def cagr(start, end, n_years: int):
    """Return (value, flag). value is the CAGR % or None when an edge case fires."""
    # Insufficient history
    if start is None or end is None or n_years is None or n_years < 1:
        return None, INSUFFICIENT

    # Zero base — undefined growth
    if start == 0:
        return None, ZERO_BASE

    # Sign-based edge cases
    if start < 0 and end < 0:
        return None, BOTH_NEGATIVE
    if start < 0 and end > 0:
        return None, TURNAROUND
    if start > 0 and end < 0:
        return None, DECLINE_TO_LOSS

    # Normal: both positive
    value = ((end / start) ** (1 / n_years) - 1) * 100
    return value, NORMAL


def cagr_from_series(series: list, n_years: int):
    """Compute CAGR over the last n_years of a chronological value list.

    series is oldest->newest. Returns (value, flag).
    Needs at least n_years+1 points; otherwise INSUFFICIENT.
    """
    if series is None or len(series) < n_years + 1:
        return None, INSUFFICIENT
    start = series[-(n_years + 1)]
    end = series[-1]
    return cagr(start, end, n_years)
