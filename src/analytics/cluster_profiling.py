"""Cluster profiling, correlation heatmap, outlier detection, portfolio stats
(Sprint 6, Day 37).

Run:  python -m src.analytics.cluster_profiling
"""

import os
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from dotenv import load_dotenv

from .clustering import FEATURES

KPI_10 = [
    "return_on_equity_pct", "return_on_capital_employed_pct", "net_profit_margin_pct",
    "operating_profit_margin_pct", "debt_to_equity", "interest_coverage",
    "asset_turnover", "revenue_cagr_5yr", "pat_cagr_5yr", "free_cash_flow_cr",
]


def profile_clusters(fr_latest: pd.DataFrame, cluster_labels: pd.DataFrame) -> pd.DataFrame:
    """Mean and median of each feature per cluster."""
    df = fr_latest.merge(cluster_labels[["company_id", "cluster_id", "cluster_name"]],
                         on="company_id", how="inner")
    # any clustering FEATURES missing from the real table (e.g. fcf_cagr_5yr not
    # yet computed) get a NaN column so profiling doesn't crash
    for f in FEATURES:
        if f not in df.columns:
            df[f] = float("nan")
    agg = df.groupby(["cluster_id", "cluster_name"])[FEATURES].agg(["mean", "median"])
    agg.columns = ["_".join(c) for c in agg.columns]
    return agg.reset_index()


def correlation_heatmap(fr_latest: pd.DataFrame, out_path: str = "reports/correlation_heatmap.png"):
    available = [k for k in KPI_10 if k in fr_latest.columns]
    corr = fr_latest[available].corr(method="pearson")

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0,
               square=True, ax=ax, cbar_kws={"shrink": 0.8})
    ax.set_title("Pearson Correlation — 10 KPIs (Latest Year)")
    fig.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return corr


def detect_outliers(fr_latest: pd.DataFrame, sectors: pd.DataFrame,
                    z_threshold: float = 3.0) -> pd.DataFrame:
    """Z-score per metric within each broad_sector; flag |Z| > threshold."""
    df = fr_latest.merge(sectors, on="company_id", how="left")
    available = [k for k in KPI_10 if k in df.columns]

    rows = []
    for sector, grp in df.groupby("broad_sector"):
        for metric in available:
            vals = grp[metric]
            mean, std = vals.mean(), vals.std()
            if pd.isna(std) or std == 0:
                continue
            z = (vals - mean) / std
            flagged = grp[z.abs() > z_threshold]
            for idx in flagged.index:
                rows.append({
                    "company_id": df.loc[idx, "company_id"],
                    "metric": metric,
                    "value": round(df.loc[idx, metric], 3),
                    "z_score": round(z.loc[idx], 3),
                    "sector": sector,
                    "sector_mean": round(mean, 3),
                    "sector_std": round(std, 3),
                })
    return pd.DataFrame(rows, columns=["company_id", "metric", "value", "z_score",
                                       "sector", "sector_mean", "sector_std"])


def portfolio_stats(fr_latest: pd.DataFrame) -> pd.DataFrame:
    available = [k for k in KPI_10 if k in fr_latest.columns]
    rows = []
    for metric in available:
        vals = fr_latest[metric].dropna()
        if vals.empty:
            continue
        rows.append({
            "metric": metric,
            "P10": round(vals.quantile(0.10), 3),
            "P25": round(vals.quantile(0.25), 3),
            "P50": round(vals.quantile(0.50), 3),
            "P75": round(vals.quantile(0.75), 3),
            "P90": round(vals.quantile(0.90), 3),
            "Mean": round(vals.mean(), 3),
            "Std": round(vals.std(), 3),
        })
    return pd.DataFrame(rows)


def main():
    load_dotenv()
    db = os.getenv("DB_PATH", "data/nifty100.db")
    conn = sqlite3.connect(db)

    fr = pd.read_sql("SELECT * FROM financial_ratios ORDER BY company_id, year", conn)
    fr_latest = fr.sort_values("year").groupby("company_id").tail(1).reset_index(drop=True)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    conn.close()

    cluster_path = Path("output/cluster_labels.csv")
    if not cluster_path.exists():
        raise FileNotFoundError("output/cluster_labels.csv not found — run Day 36 (clustering.py) first.")
    cluster_labels = pd.read_csv(cluster_path)

    # --- cluster profiling ---
    profile = profile_clusters(fr_latest, cluster_labels)
    print("--- Cluster profiles (mean of key features) ---")
    mean_cols = ["cluster_name"] + [f"{f}_mean" for f in FEATURES]
    print(profile[mean_cols].to_string(index=False))

    # --- correlation heatmap ---
    corr = correlation_heatmap(fr_latest)
    print(f"\nCorrelation heatmap saved -> reports/correlation_heatmap.png ({corr.shape[0]}x{corr.shape[1]} KPIs)")

    # --- outlier detection ---
    outliers = detect_outliers(fr_latest, sectors)
    Path("output").mkdir(exist_ok=True)
    outliers.to_csv("output/outlier_report.csv", index=False)
    print(f"\noutlier_report.csv: {len(outliers)} outlier entries (|Z| > 3)")
    if not outliers.empty:
        print(outliers.head(10).to_string(index=False))

    # --- portfolio stats ---
    stats = portfolio_stats(fr_latest)
    stats.to_csv("output/portfolio_stats.csv", index=False)
    print(f"\nportfolio_stats.csv: {len(stats)} metrics summarised")
    print(stats.to_string(index=False))


if __name__ == "__main__":
    main()
