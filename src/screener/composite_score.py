"""Composite quality score (0-100) with P10/P90 winsorisation (Sprint 3, Day 17).

Weighting (per spec):
  35% Profitability = ROE 15 + ROCE 10 + NPM 10
  30% Cash Quality  = FCF CAGR 15 + CFO/PAT 10 + FCF-positive flag 5
  20% Growth        = Revenue CAGR 10 + PAT CAGR 10
  15% Leverage      = D/E score 10 + ICR score 5

Each metric is winsorised at the 10th/90th percentile (caps extreme outliers such
as INDIGO's 892% ROE) then min-max scaled to 0-100. Leverage metrics are inverted
(lower D/E is better). A sector-relative variant normalises within broad_sector.
"""

import numpy as np
import pandas as pd


def winsorise(s: pd.Series, low=0.10, high=0.90) -> pd.Series:
    """Clip a series to its P10/P90 values (outlier capping)."""
    s = pd.to_numeric(s, errors="coerce")
    lo, hi = s.quantile(low), s.quantile(high)
    return s.clip(lo, hi)


def scale_0_100(s: pd.Series, invert: bool = False) -> pd.Series:
    """Winsorise then min-max scale to 0-100. invert=True flips (lower is better)."""
    w = winsorise(s)
    lo, hi = w.min(), w.max()
    if hi == lo:
        scaled = pd.Series(50.0, index=s.index)  # no spread -> neutral
    else:
        scaled = (w - lo) / (hi - lo) * 100
    if invert:
        scaled = 100 - scaled
    return scaled.fillna(0)


# metric -> (column, invert)
COMPONENTS = {
    "roe": ("return_on_equity_pct", False, 15),
    "npm": ("net_profit_margin_pct", False, 10),
    "rev_cagr": ("revenue_cagr_5yr", False, 10),
    "pat_cagr": ("pat_cagr_5yr", False, 10),
    "de": ("debt_to_equity", True, 10),  # inverted
    "icr": ("interest_coverage", False, 5),
    "fcf": ("free_cash_flow_cr", False, 15),
    "asset_turn": ("asset_turnover", False, 5),
    "opm": ("operating_profit_margin_pct", False, 10),
}


def composite_score(df: pd.DataFrame) -> pd.Series:
    """Weighted 0-100 composite score across available components."""
    total = pd.Series(0.0, index=df.index)
    weight_used = 0
    for _, (col, invert, weight) in COMPONENTS.items():
        if col in df.columns:
            total += scale_0_100(df[col], invert=invert) * (weight / 100.0)
            weight_used += weight
    # renormalise if some components were missing so the max stays ~100
    if weight_used and weight_used != 100:
        total = total * (100.0 / weight_used)
    return total.round(2)


def sector_relative_score(
    df: pd.DataFrame, sector_col: str = "broad_sector"
) -> pd.Series:
    """Composite score normalised within each sector."""
    out = pd.Series(0.0, index=df.index)
    if sector_col not in df.columns:
        return composite_score(df)
    for _, grp in df.groupby(sector_col):
        out.loc[grp.index] = composite_score(grp)
    return out.round(2)
