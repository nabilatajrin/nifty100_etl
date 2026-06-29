"""Unit tests for cash-flow KPIs + capital allocation (Sprint 2, Day 11)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from analytics.cashflow_kpis import (
    free_cash_flow, cfo_quality_score, capex_intensity,
    fcf_conversion_rate, capital_allocation_pattern,
)


def test_fcf_normal():
    # 100 + (-30) = 70
    assert free_cash_flow(100, -30) == 70

def test_fcf_negative_allowed():
    # 20 + (-50) = -30 (allowed)
    assert free_cash_flow(20, -50) == -30

def test_cfo_quality_high():
    val, label = cfo_quality_score([120, 130], [100, 100])
    assert label == "High Quality"

def test_cfo_quality_accrual_risk():
    val, label = cfo_quality_score([30, 40], [100, 100])
    assert label == "Accrual Risk"

def test_cfo_quality_zero_pat_skipped():
    # both PAT zero -> no usable year -> (None, None)
    val, label = cfo_quality_score([50, 60], [0, 0])
    assert val is None and label is None

def test_capex_asset_light():
    # |−2| / 100 * 100 = 2% -> Asset Light
    val, label = capex_intensity(-2, 100)
    assert label == "Asset Light"

def test_capex_capital_intensive():
    # |−15| / 100 * 100 = 15% -> Capital Intensive
    val, label = capex_intensity(-15, 100)
    assert label == "Capital Intensive"

def test_fcf_conversion_zero_opprofit_none():
    assert fcf_conversion_rate(50, 0) is None

def test_capital_alloc_reinvestor():
    so, si, sf, label = capital_allocation_pattern(100, -40, -20)
    assert (so, si, sf) == ("+", "-", "-")
    assert label == "Reinvestor"

def test_capital_alloc_distress():
    so, si, sf, label = capital_allocation_pattern(-50, 10, 60)
    assert label == "Distress Signal"

def test_capital_alloc_shareholder_returns():
    # (+,-,-) with high CFO/PAT -> Shareholder Returns
    so, si, sf, label = capital_allocation_pattern(100, -40, -20, cfo_pat_ratio=2.0)
    assert label == "Shareholder Returns"
