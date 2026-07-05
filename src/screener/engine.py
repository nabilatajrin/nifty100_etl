"""Screener filter engine (Sprint 3, Day 15).

Loads screener_config.yaml and applies threshold filters to the financial_ratios
DataFrame. Two special rules:
  - D/E filter skips Financials-sector companies (high leverage is normal).
  - "Debt Free" (ICR is None) is treated as ICR = infinity: always passes any
    ICR minimum.
Returns a filtered, sorted DataFrame with a composite_quality_score column.
"""

from pathlib import Path
import yaml
import numpy as np
import pandas as pd

FINANCIALS = "Financials"


def load_config(path: str | Path = "config/screener_config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def _apply_one_filter(df: pd.DataFrame, meta: dict, threshold, metric_key: str,
                      sectors: pd.Series) -> pd.Series:
    """Return a boolean mask for one metric filter."""
    col = meta["column"]
    direction = meta["direction"]

    if col not in df.columns:
        # metric not available in the data -> treat as pass-through (no filtering)
        return pd.Series(True, index=df.index)

    value = df[col]
    keep = pd.Series(True, index=df.index)

    if direction == "min":
        # ICR special-case: None (Debt Free) is treated as +inf -> always passes
        if metric_key == "icr":
            keep = value.isna() | (value >= threshold)
        else:
            keep = value.notna() & (value >= threshold)
    else:  # max
        keep = value.notna() & (value <= threshold)

    # D/E special-case: skip (always keep) Financials-sector companies
    if metric_key == "de":
        is_financial = sectors.reindex(df.index).eq(FINANCIALS)
        keep = keep | is_financial

    return keep


def apply_filters(df: pd.DataFrame, thresholds: dict, config: dict,
                  sectors: pd.Series) -> pd.DataFrame:
    """Apply a dict of {metric_key: threshold} filters. Returns filtered rows."""
    mask = pd.Series(True, index=df.index)
    metrics = config["metrics"]

    for metric_key, threshold in thresholds.items():
        if metric_key not in metrics:
            continue
        mask &= _apply_one_filter(df, metrics[metric_key], threshold,
                                  metric_key, sectors)

    result = df[mask].copy()
    if "composite_quality_score" in result.columns:
        result = result.sort_values("composite_quality_score", ascending=False)
    return result


def run_preset(df: pd.DataFrame, preset_name: str, config: dict,
               sectors: pd.Series) -> pd.DataFrame:
    """Run a named preset from the config."""
    thresholds = config["presets"][preset_name]
    return apply_filters(df, thresholds, config, sectors)
