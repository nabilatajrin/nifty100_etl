"""Unit tests for leverage & efficiency ratios (Sprint 2, Day 9) — 8 cases."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from analytics.ratios import (
    debt_to_equity, high_leverage_flag, interest_coverage, icr_label,
    icr_warning_flag, net_debt, asset_turnover,
)


def test_de_normal():
    # 100 / (200 + 300) = 0.2
    assert debt_to_equity(100, 200, 300) == 0.2

def test_de_debtfree_returns_zero():
    # borrowings == 0 -> 0 (NOT None)
    assert debt_to_equity(0, 200, 300) == 0

def test_high_leverage_flag_nonfinancial():
    # D/E 6 for an IT company -> flagged
    assert high_leverage_flag(6, "Information Technology") is True

def test_high_leverage_flag_suppressed_for_financials():
    # D/E 6 for a bank -> NOT flagged (structurally normal)
    assert high_leverage_flag(6, "Financials") is False

def test_icr_interest_zero_none():
    assert interest_coverage(50, 5, 0) is None

def test_icr_label_debt_free():
    assert icr_label(None) == "Debt Free"

def test_icr_warning_below_threshold():
    # ICR = (10 + 0) / 8 = 1.25 < 1.5 -> warning True
    assert icr_warning_flag(interest_coverage(10, 0, 8)) is True

def test_asset_turnover_zero_assets_none():
    assert asset_turnover(100, 0) is None
