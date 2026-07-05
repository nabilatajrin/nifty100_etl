"""Unit tests for the screener filter engine (Sprint 3, Day 15)."""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from screener import engine

CONFIG = Path(__file__).resolve().parents[2] / "config" / "screener_config.yaml"


def _sample():
    df = pd.DataFrame({
        "company_id": ["TCS", "HDFCBANK", "INFY", "WEAKCO"],
        "return_on_equity_pct": [50, 16, 25, 8],
        "debt_to_equity": [0.1, 8.0, 0.0, 0.5],
        "free_cash_flow_cr": [100, 50, 80, -10],
        "revenue_cagr_5yr": [12, 20, 15, 5],
        "interest_coverage": [None, 3.0, None, 1.2],
        "composite_quality_score": [90, 70, 85, 30],
    })
    sectors = pd.Series(["IT", "Financials", "IT", "IT"], index=df.index)
    return df, sectors


def test_de_carveout_keeps_financials():
    df, sectors = _sample()
    cfg = engine.load_config(CONFIG)
    res = engine.run_preset(df, "quality_compounder", cfg, sectors)
    # HDFCBANK has D/E 8 but is Financials -> should still pass
    assert "HDFCBANK" in res["company_id"].tolist()

def test_debt_free_passes_icr_min():
    df, sectors = _sample()
    cfg = engine.load_config(CONFIG)
    res = engine.apply_filters(df, {"icr": 2.0}, cfg, sectors)
    # TCS & INFY are Debt Free (ICR None) -> pass; WEAKCO (1.2) fails
    ids = res["company_id"].tolist()
    assert "TCS" in ids and "INFY" in ids and "WEAKCO" not in ids

def test_weakco_filtered_out():
    df, sectors = _sample()
    cfg = engine.load_config(CONFIG)
    res = engine.run_preset(df, "quality_compounder", cfg, sectors)
    # WEAKCO: ROE 8 (<15), negative FCF -> filtered out
    assert "WEAKCO" not in res["company_id"].tolist()

def test_result_sorted_by_composite():
    df, sectors = _sample()
    cfg = engine.load_config(CONFIG)
    res = engine.run_preset(df, "quality_compounder", cfg, sectors)
    scores = res["composite_quality_score"].tolist()
    assert scores == sorted(scores, reverse=True)
