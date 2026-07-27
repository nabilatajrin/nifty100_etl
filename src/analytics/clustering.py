"""KMeans clustering of the 92 companies by financial profile (Sprint 6, Day 36).

Features: return_on_equity_pct, debt_to_equity, revenue_cagr_5yr, fcf_cagr_5yr,
operating_profit_margin_pct. Missing values imputed with the sector median
before scaling. StandardScaler + KMeans(n_clusters=5, random_state=42).

Run:  python -m src.analytics.clustering
"""

import os
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]
N_CLUSTERS = 5
RANDOM_STATE = 42


def load_features(conn) -> pd.DataFrame:
    fr = pd.read_sql("SELECT * FROM financial_ratios ORDER BY company_id, year", conn)
    latest = fr.sort_values("year").groupby("company_id").tail(1).reset_index(drop=True)

    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    df = latest.merge(sectors, on="company_id", how="left")

    # fcf_cagr_5yr may not exist yet in financial_ratios -> compute a fallback of NaN
    for f in FEATURES:
        if f not in df.columns:
            df[f] = np.nan

    return df[["company_id", "broad_sector"] + FEATURES]


def impute_sector_median(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing feature values with that company's sector median (fallback:
    the overall median if the whole sector is missing that feature; final
    fallback: 0 if the entire feature column is missing everywhere)."""
    out = df.copy()
    for f in FEATURES:
        sector_median = out.groupby("broad_sector")[f].transform("median")
        out[f] = out[f].fillna(sector_median)
        overall_median = out[f].median()
        out[f] = out[f].fillna(overall_median if pd.notna(overall_median) else 0)
    return out


def run_kmeans(df: pd.DataFrame) -> tuple:
    """Returns (labels, distances_to_own_centroid, fitted_kmeans, scaler)."""
    X = df[FEATURES].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    km = KMeans(n_clusters=N_CLUSTERS, random_state=RANDOM_STATE, n_init=10)
    labels = km.fit_predict(X_scaled)

    distances = np.linalg.norm(X_scaled - km.cluster_centers_[labels], axis=1)
    return labels, distances, km, scaler


def elbow_plot(df: pd.DataFrame, out_path: str = "reports/elbow_plot.png") -> dict:
    X = df[FEATURES].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    inertias = {}
    for k in range(2, 11):
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        km.fit(X_scaled)
        inertias[k] = km.inertia_

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(list(inertias.keys()), list(inertias.values()), marker="o")
    ax.axvline(5, color="red", linestyle="--", label="k=5 (chosen)")
    ax.set_xlabel("Number of clusters (k)")
    ax.set_ylabel("Inertia")
    ax.set_title("KMeans Elbow Plot")
    ax.legend()
    fig.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return inertias


# Descriptive names assigned by profiling cluster centroids (Day 37 refines
# these against real data; placeholder ordering here by centroid quality proxy).
CLUSTER_NAME_TEMPLATE = [
    "High-Quality Compounders",
    "Defensive Dividend Payers",
    "Value Cyclicals",
    "Distressed or Turnaround",
    "Emerging Growth",
]


def name_clusters(df: pd.DataFrame, labels: np.ndarray) -> dict:
    """Rank clusters by mean ROE (proxy for quality) and assign template names
    in that order — Day 37 will refine based on full profiling."""
    tmp = df.copy()
    tmp["cluster_id"] = labels
    ranked = (
        tmp.groupby("cluster_id")["return_on_equity_pct"]
        .mean()
        .sort_values(ascending=False)
    )
    return {cid: CLUSTER_NAME_TEMPLATE[i] for i, cid in enumerate(ranked.index)}


def main():
    load_dotenv()
    db = os.getenv("DB_PATH", "data/nifty100.db")
    conn = sqlite3.connect(db)
    raw = load_features(conn)
    conn.close()

    df = impute_sector_median(raw)

    inertias = elbow_plot(df)
    print("Elbow inertias (k: inertia):")
    for k, v in inertias.items():
        print(f"  k={k}: {v:.1f}")

    labels, distances, km, scaler = run_kmeans(df)
    names = name_clusters(df, labels)

    out = pd.DataFrame(
        {
            "company_id": df["company_id"],
            "cluster_id": labels,
            "cluster_name": [names[c] for c in labels],
            "distance_from_centroid": np.round(distances, 4),
        }
    )

    out_path = Path("output/cluster_labels.csv")
    out_path.parent.mkdir(exist_ok=True)
    out.to_csv(out_path, index=False)

    print(f"\ncluster_labels.csv: {len(out)} companies assigned")
    print(out["cluster_name"].value_counts().to_string())
    print(f"\nAny company missing a cluster_id: {out['cluster_id'].isna().sum()}")


if __name__ == "__main__":
    main()
