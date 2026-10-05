"""02-operations-311 — 01_analysis.py

Ops KPIs: backlog, closure rate, resolution time, weekend/hour load, worst types.

Outputs: data/processed/cases_clean.csv, outputs/kpis.json + seg CSVs + charts
"""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

_shared_root = Path(__file__).resolve().parent
while _shared_root != _shared_root.parent and not (_shared_root / "shared").is_dir():
    _shared_root = _shared_root.parent
sys.path.insert(0, str(_shared_root))  # callable from repo root or standalone checkout
from shared.utils import mpl_setup, save_png, save_json   # noqa: E402

PROJECT = Path(__file__).resolve().parent.parent
mpl_setup()


def main() -> None:
    df = pd.read_csv(PROJECT / "data" / "raw" / "nyc311_2026Q3.csv")
    df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
    df["closed_date"] = pd.to_datetime(df["closed_date"], errors="coerce")
    df = df.dropna(subset=["created_date"]).copy()
    df["open"] = df["closed_date"].isna().astype(int)
    df["resolve_h"] = (df["closed_date"] - df["created_date"]).dt.total_seconds() / 3600
    df.loc[df["open"] == 1, "resolve_h"] = np.nan
    df["dow"] = df["created_date"].dt.dayofweek
    df["hour"] = df["created_date"].dt.hour
    df["agency_name"] = df["agency_name"].fillna("Unknown")
    df["borough"] = df["borough"].fillna("Unspecified")

    (PROJECT / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (OUT := PROJECT / "outputs").mkdir(parents=True, exist_ok=True)
    df.to_csv(PROJECT / "data" / "processed" / "cases_clean.csv", index=False)

    res = df.loc[df.open == 0, "resolve_h"]
    kpis = {
        "cases": int(len(df)),
        "closed": int((df.open == 0).sum()),
        "backlog_pct": round(float(df.open.mean()), 4),
        "median_resolve_h": round(float(res.median()), 1),
        "p90_resolve_h": round(float(res.quantile(.9)), 1),
        "share_over_72h": round(float((res > 72).mean()), 4),
        "worst_agency_name": str(df.groupby("agency_name").apply(
            lambda g: pd.Series(g.resolve_h.median().iloc[0], index=[0]),
            include_groups=False).idxmax()[0] if False else ""),
    }
    # worst agencies by median resolution (min 500 cases)
    ag = df[df.open == 0].groupby("agency_name").agg(
        cases=("unique_key", "count"), med_h=("resolve_h", "median")).query("cases>=500")
    kpis["worst_agency"] = str(ag.med_h.idxmax())
    kpis["worst_agency_med_h"] = float(ag.med_h.max())
    kpis["best_agency"] = str(ag.med_h.idxmin())
    kpis["best_agency_med_h"] = float(ag.med_h.min())
    kpis["n_over_72h"] = int((res > 72).sum())
    save_json(kpis, PROJECT / "outputs" / "kpis.json")

    ag.round(1).to_csv(PROJECT / "outputs" / "seg_agency.csv")
    tp = df.groupby("complaint_type").agg(
        cases=("unique_key", "count"), med_h=("resolve_h", "median"),
        backlog=("open", "mean"), over_72h=("resolve_h", lambda s: float((s.dropna() > 72).mean()))
    ).round(3).sort_values("cases", ascending=False).head(15)
    tp.to_csv(PROJECT / "outputs" / "seg_types.csv")
    bo = df.groupby("borough").agg(cases=("unique_key", "count"),
                                   med_h=("resolve_h", "median"),
                                   backlog=("open", "mean")).round(3)
    bo.to_csv(PROJECT / "outputs" / "seg_borough.csv")
    heat = df.pivot_table(index="dow", columns="hour", values="unique_key",
                          aggfunc="count", fill_value=0)
    heat.to_csv(PROJECT / "outputs" / "seg_dowhour.csv")

    # charts
    import matplotlib.pyplot as plt
    TECH = "#134e5e"
    fig, ax = plt.subplots(figsize=(7.2, 4))
    top10 = ag.sort_values("med_h").tail(10)
    ax.barh(top10.index, top10.med_h, color=TECH)
    ax.set_xlabel("Median resolution time (hours)")
    ax.set_title("Slowest service agencies (n≥500 cases)")
    save_png(fig, PROJECT / "outputs" / "charts" / "slowest_agencies.png")

    fig, ax = plt.subplots(figsize=(7.2, 4))
    hours = df.groupby("hour").size()
    ax.bar(hours.index, hours.values / hours.sum(), color="#0e7490")
    ax.set_xlabel("Hour of day"); ax.set_ylabel("Share of complaint volume")
    ax.set_title("Complaint arrivals by hour — evening peak drives backlog")
    save_png(fig, PROJECT / "outputs" / "charts" / "arrivals_hour.png")
    print(json.dumps(kpis, indent=2))


if __name__ == "__main__":
    main()
