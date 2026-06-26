"""Unit tests for profitability ratios (Sprint 2, Day 8) — 8 cases."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from analytics.ratios import (
    net_profit_margin, operating_profit_margin, opm_cross_check,
    return_on_equity, return_on_capital_employed, return_on_assets,
)


def test_npm_normal():
    # 20 / 100 * 100 = 20
    assert net_profit_margin(20, 100) == 20.0

def test_npm_zero_sales_none():
    assert net_profit_margin(20, 0) is None

def test_roe_normal():
    # 100 / (200 + 300) * 100 = 20
    assert return_on_equity(100, 200, 300) == 20.0

def test_roe_negative_equity_none():
    # equity + reserves = -50 <= 0 -> None
    assert return_on_equity(100, 10, -60) is None

def test_roa_zero_assets_none():
    assert return_on_assets(50, 0) is None

def test_roce_normal():
    # EBIT = 50 - 10 = 40; capital = 100+200+100 = 400; 40/400*100 = 10
    assert return_on_capital_employed(50, 10, 100, 200, 100) == 10.0

def test_opm_normal():
    # 30 / 120 * 100 = 25
    assert round(operating_profit_margin(30, 120), 2) == 25.0

def test_opm_cross_check_mismatch():
    # computed 25, source 30 -> diff 5 > 1 -> flagged True
    assert opm_cross_check(25.0, 30.0) is True
