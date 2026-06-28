"""Unit tests for the CAGR engine (Sprint 2, Day 10) — 10 cases."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from analytics.cagr import (
    cagr, cagr_from_series,
    DECLINE_TO_LOSS, TURNAROUND, BOTH_NEGATIVE, ZERO_BASE, INSUFFICIENT,
)


def test_cagr_normal():
    # (161/100)^(1/5) - 1 ~ 10%
    val, flag = cagr(100, 161, 5)
    assert round(val, 1) == 10.0
    assert flag is None

def test_cagr_doubling():
    # (200/100)^(1/1) - 1 = 100%
    val, flag = cagr(100, 200, 1)
    assert round(val, 1) == 100.0
    assert flag is None

def test_cagr_turnaround():
    val, flag = cagr(-100, 200, 5)
    assert val is None
    assert flag == TURNAROUND

def test_cagr_decline_to_loss():
    val, flag = cagr(100, -50, 5)
    assert val is None
    assert flag == DECLINE_TO_LOSS

def test_cagr_both_negative():
    val, flag = cagr(-100, -50, 5)
    assert val is None
    assert flag == BOTH_NEGATIVE

def test_cagr_zero_base():
    val, flag = cagr(0, 100, 5)
    assert val is None
    assert flag == ZERO_BASE

def test_cagr_insufficient_nyears():
    val, flag = cagr(100, 200, 0)
    assert val is None
    assert flag == INSUFFICIENT

def test_cagr_none_input():
    val, flag = cagr(None, 200, 5)
    assert val is None
    assert flag == INSUFFICIENT

def test_cagr_from_series_normal():
    # 6 points -> 5yr window; 100 -> 161
    series = [100, 110, 120, 135, 150, 161]
    val, flag = cagr_from_series(series, 5)
    assert round(val, 1) == 10.0
    assert flag is None

def test_cagr_from_series_insufficient():
    # only 3 points, need 6 for a 5yr CAGR
    series = [100, 110, 120]
    val, flag = cagr_from_series(series, 5)
    assert val is None
    assert flag == INSUFFICIENT
