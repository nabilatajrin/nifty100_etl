"""Unit tests for normaliser — 20 year cases + 15 ticker cases (Sprint 1, Day 2)."""

import sys
from pathlib import Path

# Make src importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from etl.normaliser import normalize_year, normalize_ticker, PARSE_ERROR


# ---------------- normalize_year: 20 cases ----------------

def test_year_mar23():
    assert normalize_year("Mar-23") == "2023-03"

def test_year_mar_space_23():
    assert normalize_year("Mar 23") == "2023-03"

def test_year_full_month():
    assert normalize_year("March-2023") == "2023-03"

def test_year_plain_int():
    assert normalize_year("2023") == "2023-03"

def test_year_fy23():
    assert normalize_year("FY23") == "2023-03"

def test_year_fy24():
    assert normalize_year("FY24") == "2024-03"

def test_year_fy_full():
    assert normalize_year("FY2023") == "2023-03"

def test_year_fy_space():
    assert normalize_year("FY 24") == "2024-03"

def test_year_dec22():
    assert normalize_year("Dec-22") == "2022-12"

def test_year_jun23():
    assert normalize_year("Jun-23") == "2023-06"

def test_year_already_normalised():
    assert normalize_year("2023-03") == "2023-03"

def test_year_already_normalised_dec():
    assert normalize_year("2022-12") == "2022-12"

def test_year_full_month_lower():
    assert normalize_year("december-2021") == "2021-12"

def test_year_leading_trailing_space():
    assert normalize_year("  Mar-23  ") == "2023-03"

def test_year_sep():
    assert normalize_year("Sep-20") == "2020-09"

def test_year_jan_full_year():
    assert normalize_year("Jan-2019") == "2019-01"

def test_year_year_then_month():
    assert normalize_year("2023-Mar") == "2023-03"

def test_year_garbage():
    assert normalize_year("xyz") == PARSE_ERROR

def test_year_empty():
    assert normalize_year("") == PARSE_ERROR

def test_year_none():
    assert normalize_year(None) == PARSE_ERROR


# ---------------- normalize_ticker: 15 cases ----------------

def test_ticker_plain():
    assert normalize_ticker("TCS") == "TCS"

def test_ticker_lower():
    assert normalize_ticker("tcs") == "TCS"

def test_ticker_strip():
    assert normalize_ticker("  TCS  ") == "TCS"

def test_ticker_mixed_case():
    assert normalize_ticker("Infy") == "INFY"

def test_ticker_hyphen():
    assert normalize_ticker("BAJAJ-AUTO") == "BAJAJ-AUTO"

def test_ticker_hyphen_lower():
    assert normalize_ticker("bajaj-auto") == "BAJAJ-AUTO"

def test_ticker_ampersand():
    assert normalize_ticker("M&M") == "M&M"

def test_ticker_ampersand_lower():
    assert normalize_ticker("m&m") == "M&M"

def test_ticker_strip_and_upper():
    assert normalize_ticker("  hdfcbank ") == "HDFCBANK"

def test_ticker_already_upper():
    assert normalize_ticker("RELIANCE") == "RELIANCE"

def test_ticker_tabs():
    assert normalize_ticker("\tSBIN\t") == "SBIN"

def test_ticker_long_name():
    assert normalize_ticker("bajfinance") == "BAJFINANCE"

def test_ticker_none():
    assert normalize_ticker(None) == ""

def test_ticker_empty():
    assert normalize_ticker("") == ""

def test_ticker_numeric_suffix():
    assert normalize_ticker("m&mfin") == "M&MFIN"
