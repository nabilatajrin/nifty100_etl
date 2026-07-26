"""Auto pros/cons generator (Sprint 5, Day 30).

Each rule inspects a company's multi-year financial_ratios (+ balance sheet /
cash flow where needed) history and, if triggered, returns (confidence_pct,
text). Only entries with confidence > 60 are kept in the output.

Run:  python -m src.nlp.pros_cons_generator
"""

import os
import sqlite3
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

MIN_CONFIDENCE = 60


def _consecutive_trend(series: pd.Series, n: int, improving: bool = True) -> bool:
    """True if the last n values are monotonically improving (or declining),
    with at least one genuine change (a perfectly flat series is neither)."""
    if len(series) < n:
        return False
    tail = series.tail(n).tolist()
    if any(pd.isna(v) for v in tail):
        return False
    if len(set(tail)) == 1:  # perfectly flat -> not a trend either way
        return False
    if improving:
        return all(tail[i] <= tail[i + 1] for i in range(len(tail) - 1))
    return all(tail[i] >= tail[i + 1] for i in range(len(tail) - 1))


# ============================== PRO RULES ==============================

def pro_01_high_roe(h: pd.DataFrame):
    if len(h) < 3:
        return None
    tail = h["return_on_equity_pct"].tail(3)
    if tail.notna().all() and (tail > 20).all():
        return 90, "Consistently high return on equity above 20% demonstrates exceptional capital efficiency"
    return None


def pro_02_fcf_positive_5yr(h: pd.DataFrame):
    if len(h) < 5:
        return None
    tail = h["free_cash_flow_cr"].tail(5)
    if tail.notna().all() and (tail > 0).all():
        return 85, "Strong free cash flow generation over 5 years signals healthy business fundamentals"
    return None


def pro_03_debt_free(h: pd.DataFrame):
    latest = h.iloc[-1]
    if pd.notna(latest.get("debt_to_equity")) and latest["debt_to_equity"] == 0:
        return 95, "Debt-free balance sheet provides financial flexibility and eliminates interest burden"
    return None


def pro_04_revenue_cagr(h: pd.DataFrame):
    latest = h.iloc[-1]
    v = latest.get("revenue_cagr_5yr")
    if pd.notna(v) and v > 15:
        return 80, "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum"
    return None


def pro_05_opm(h: pd.DataFrame):
    latest = h.iloc[-1]
    v = latest.get("operating_profit_margin_pct")
    if pd.notna(v) and v > 25:
        return 80, "Operating profit margin above 25% indicates strong pricing power and cost discipline"
    return None


def pro_06_pat_cagr(h: pd.DataFrame):
    latest = h.iloc[-1]
    v = latest.get("pat_cagr_5yr")
    if pd.notna(v) and v > 20:
        return 85, "Net profit compounding at above 20% over 5 years creates significant shareholder value"
    return None


def pro_07_icr(h: pd.DataFrame):
    latest = h.iloc[-1]
    icr = latest.get("interest_coverage")
    if pd.isna(icr) or (pd.notna(icr) and icr > 10):
        return 75, "Very high interest coverage ratio reflects negligible financial stress from debt servicing"
    return None


def pro_08_dividend_fcf(h: pd.DataFrame):
    latest = h.iloc[-1]
    div = latest.get("dividend_payout_ratio_pct")
    fcf = latest.get("free_cash_flow_cr")
    if pd.notna(div) and pd.notna(fcf) and div > 0 and fcf > 0:
        # dividend_payout_ratio doesn't directly give yield; treat >0 payout + positive FCF as the proxy signal
        return 65, "Consistent dividend payout backed by positive free cash flow"
    return None


def pro_09_eps_cagr(h: pd.DataFrame):
    latest = h.iloc[-1]
    v = latest.get("eps_cagr_5yr")
    if pd.notna(v) and v > 15:
        return 80, "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding"
    return None


def pro_10_roe_improving(h: pd.DataFrame):
    if len(h) < 3:
        return None
    if _consecutive_trend(h["return_on_equity_pct"], 3, improving=True):
        return 70, "Return on equity improving for 3 consecutive years shows strengthening business quality"
    return None


def pro_11_operating_leverage(h: pd.DataFrame):
    latest = h.iloc[-1]
    rev = latest.get("revenue_cagr_5yr")
    pat = latest.get("pat_cagr_5yr")
    if pd.notna(rev) and pd.notna(pat) and pat > rev and rev > 0:
        return 65, "Revenue growing slower than profits shows improving operating leverage and scale benefits"
    return None


def pro_12_asset_growth_declining_debt(bs_h: pd.DataFrame):
    if len(bs_h) < 2:
        return None
    assets_growing = bs_h["total_assets"].iloc[-1] > bs_h["total_assets"].iloc[-2]
    debt_declining = bs_h["borrowings"].iloc[-1] < bs_h["borrowings"].iloc[-2]
    if assets_growing and debt_declining:
        return 70, "Growing asset base funded by internal accruals reflects self-sustaining growth"
    return None


PRO_RULES_RATIO = [pro_01_high_roe, pro_02_fcf_positive_5yr, pro_03_debt_free,
                   pro_04_revenue_cagr, pro_05_opm, pro_06_pat_cagr, pro_07_icr,
                   pro_08_dividend_fcf, pro_09_eps_cagr, pro_10_roe_improving,
                   pro_11_operating_leverage]
PRO_RULES_BS = [pro_12_asset_growth_declining_debt]


# ============================== CON RULES ==============================

def con_01_high_de(h: pd.DataFrame, sector: str):
    latest = h.iloc[-1]
    de = latest.get("debt_to_equity")
    if sector != "Financials" and pd.notna(de) and de > 2.0:
        return 85, f"Debt-to-equity ratio of {de:.2f} is elevated for a non-financial company and warrants monitoring"
    return None


def con_02_fcf_negative_3yr(h: pd.DataFrame):
    if len(h) < 3:
        return None
    tail = h["free_cash_flow_cr"].tail(3)
    if tail.notna().all() and (tail < 0).all():
        return 85, "Free cash flow negative for 3 consecutive years raises concern about cash generation quality"
    return None


def con_03_opm_declining_3yr(h: pd.DataFrame):
    if len(h) < 3:
        return None
    if _consecutive_trend(h["operating_profit_margin_pct"], 3, improving=False) and \
       h["operating_profit_margin_pct"].tail(3).iloc[0] > h["operating_profit_margin_pct"].tail(3).iloc[-1]:
        return 75, "Operating margins declining for 3 consecutive years suggest pricing or cost pressure"
    return None


def con_04_net_loss(h: pd.DataFrame):
    latest = h.iloc[-1]
    npm = latest.get("net_profit_margin_pct")
    if pd.notna(npm) and npm < 0:
        return 90, "Company reported a net loss in the most recent financial year"
    return None


def con_05_revenue_declining(pl_h: pd.DataFrame):
    if len(pl_h) < 3:
        return None
    tail = pl_h["sales"].tail(3)
    if tail.notna().all() and tail.iloc[-1] < tail.iloc[-2] < tail.iloc[0]:
        return 80, "Revenue contraction over 2 consecutive years indicates demand weakness or market share loss"
    return None


def con_06_icr_low(h: pd.DataFrame):
    latest = h.iloc[-1]
    icr = latest.get("interest_coverage")
    if pd.notna(icr) and icr < 1.5:
        return 90, "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations"
    return None


def con_07_payout_over_100(h: pd.DataFrame):
    latest = h.iloc[-1]
    payout = latest.get("dividend_payout_ratio_pct")
    if pd.notna(payout) and payout > 100:
        return 80, "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable"
    return None


def con_08_de_rising_3yr(h: pd.DataFrame):
    if len(h) < 3:
        return None
    if _consecutive_trend(h["debt_to_equity"], 3, improving=True):
        return 70, "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk"
    return None


def con_09_eps_declining_3yr(h: pd.DataFrame):
    if len(h) < 3:
        return None
    if _consecutive_trend(h["earnings_per_share"], 3, improving=False):
        return 75, "Earnings per share declining for 3 consecutive years reflects deteriorating profitability"
    return None


def con_10_roce_low(h: pd.DataFrame):
    latest = h.iloc[-1]
    roce = latest.get("return_on_capital_employed_pct")
    if pd.notna(roce) and roce < 10:
        return 70, "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital"
    return None


def con_11_net_debt_high(h: pd.DataFrame):
    latest = h.iloc[-1]
    debt = latest.get("total_debt_cr")
    fcf = latest.get("free_cash_flow_cr")  # proxy; true EBITDA not always present
    ebitda_proxy = latest.get("cash_from_operations_cr")
    if pd.notna(debt) and pd.notna(ebitda_proxy) and ebitda_proxy > 0 and debt > 3 * ebitda_proxy:
        return 65, "Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility"
    return None


def con_12_low_revenue_growth(h: pd.DataFrame):
    latest = h.iloc[-1]
    v = latest.get("revenue_cagr_5yr")
    if pd.notna(v) and v < 5:
        return 65, "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum"
    return None


CON_RULES_RATIO = [con_02_fcf_negative_3yr, con_03_opm_declining_3yr, con_04_net_loss,
                   con_06_icr_low, con_07_payout_over_100, con_08_de_rising_3yr,
                   con_09_eps_declining_3yr, con_10_roce_low, con_11_net_debt_high,
                   con_12_low_revenue_growth]
CON_RULES_SECTOR = [con_01_high_de]
CON_RULES_PL = [con_05_revenue_declining]


def generate_for_company(cid: str, ratio_h: pd.DataFrame, bs_h: pd.DataFrame,
                         pl_h: pd.DataFrame, sector: str) -> list:
    """Run every rule for one company; return list of dicts for triggered rules >60% confidence."""
    entries = []

    def _add(rule_id, kind, result):
        if result is None:
            return
        conf, text = result
        if conf > MIN_CONFIDENCE:
            entries.append({"company_id": cid, "type": kind, "rule_id": rule_id,
                            "text": text, "confidence_pct": conf})

    for i, rule in enumerate(PRO_RULES_RATIO, 1):
        _add(f"pro_{i:02d}", "pro", rule(ratio_h))
    for i, rule in enumerate(PRO_RULES_BS, 12):
        _add(f"pro_{i:02d}", "pro", rule(bs_h))

    _add("con_01", "con", con_01_high_de(ratio_h, sector))
    for i, rule in zip([2, 3, 4, 6, 7, 8, 9, 10, 11, 12], CON_RULES_RATIO):
        _add(f"con_{i:02d}", "con", rule(ratio_h))
    _add("con_05", "con", con_05_revenue_declining(pl_h))

    return entries


def main():
    load_dotenv()
    db = os.getenv("DB_PATH", "data/nifty100.db")
    conn = sqlite3.connect(db)

    ratios = pd.read_sql("SELECT * FROM financial_ratios ORDER BY company_id, year", conn)
    bs = pd.read_sql("SELECT * FROM balancesheet ORDER BY company_id, year", conn)
    pl = pd.read_sql("SELECT * FROM profitandloss ORDER BY company_id, year", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    companies = pd.read_sql("SELECT id FROM companies", conn)
    conn.close()

    sector_map = dict(zip(sectors["company_id"], sectors["broad_sector"]))

    all_entries = []
    no_pro, no_con = [], []

    for cid in companies["id"]:
        ratio_h = ratios[ratios["company_id"] == cid]
        bs_h = bs[bs["company_id"] == cid]
        pl_h = pl[pl["company_id"] == cid]
        if ratio_h.empty:
            no_pro.append(cid)
            no_con.append(cid)
            continue

        sector = sector_map.get(cid, "")
        entries = generate_for_company(cid, ratio_h, bs_h, pl_h, sector)
        all_entries.extend(entries)

        if not any(e["type"] == "pro" for e in entries):
            no_pro.append(cid)
        if not any(e["type"] == "con" for e in entries):
            no_con.append(cid)

    out = pd.DataFrame(all_entries,
                       columns=["company_id", "type", "rule_id", "text", "confidence_pct"])

    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    out.to_csv(out_dir / "pros_cons_generated.csv", index=False)

    print(f"pros_cons_generated.csv: {len(out)} entries")
    print(f"  pros: {(out['type']=='pro').sum()}  cons: {(out['type']=='con').sum()}")
    print(f"Companies with NO pro: {len(no_pro)} {no_pro[:10]}")
    print(f"Companies with NO con: {len(no_con)} {no_con[:10]}")


if __name__ == "__main__":
    main()
