"""Profitability ratio functions for the NIFTY 100 ratio engine (Sprint 2, Day 8).

Every function returns None when its denominator is zero/invalid, so callers can
store a clean NULL rather than crash on division by zero.
"""

# Sectors where high leverage is structurally normal (used by ROCE benchmarking).
FINANCIALS = "Financials"


def net_profit_margin(net_profit: float, sales: float):
    """NPM = net_profit / sales * 100. None if sales == 0."""
    if sales in (None, 0):
        return None
    return net_profit / sales * 100


def operating_profit_margin(operating_profit: float, sales: float):
    """OPM = operating_profit / sales * 100. None if sales == 0."""
    if sales in (None, 0):
        return None
    return operating_profit / sales * 100


def opm_cross_check(computed_opm, source_opm, tol: float = 1.0):
    """Return True if computed vs source OPM differ by more than `tol` (flag it)."""
    if computed_opm is None or source_opm is None:
        return False
    return abs(computed_opm - source_opm) > tol


def return_on_equity(net_profit: float, equity_capital: float, reserves: float):
    """ROE = net_profit / (equity_capital + reserves) * 100. None if equity <= 0."""
    equity = (equity_capital or 0) + (reserves or 0)
    if equity <= 0:
        return None
    return net_profit / equity * 100


def return_on_capital_employed(operating_profit: float, depreciation: float,
                               equity_capital: float, reserves: float,
                               borrowings: float):
    """ROCE = EBIT / (equity + reserves + borrowings) * 100.

    EBIT = operating_profit - depreciation. None if capital employed <= 0.
    """
    ebit = (operating_profit or 0) - (depreciation or 0)
    capital_employed = (equity_capital or 0) + (reserves or 0) + (borrowings or 0)
    if capital_employed <= 0:
        return None
    return ebit / capital_employed * 100


def return_on_assets(net_profit: float, total_assets: float):
    """ROA = net_profit / total_assets * 100. None if total_assets == 0."""
    if total_assets in (None, 0):
        return None
    return net_profit / total_assets * 100
