"""02-operations-311 — 02_bottleneck_scenarios.py

Quantifies the bottleneck and two staffing scenarios:
  A) Re-deploy: shift capacity toward the slowest heavy-volume complaint types.
  B) SLA sweep: overtime sprint to clear >72h backlog modeled at stated cost.

Outputs: outputs/scenarios.json, outputs/charts/*.png
"""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

_shared_root = Path(__file__).resolve().parent
while _shared_root != _shared_root.parent and not (_shared_root / "shared").is_dir():
    _shared_root = _shared_root.parent
sys.path.insert(0, str(_shared_root))  # callable from repo root or standalone checkout
from shared.utils import mpl_setup, save_png, save_json   # noqa: E402

PROJECT = Path(__file__).resolve().parent.parent
mpl_setup()

COST_PER_CASE_HOUR = 45.0     # $ fully-loaded cost per staff-hour (stated)
CASE_TEAM_LABOR_H = 1.6       # staff-hours of labor per case touched (stated)


def main() -> None:
    df = pd.read_csv(PROJECT / "data" / "processed" / "cases_clean.csv")
    res = df[df.open == 0]

    # top slow heavy types (volume-weighted)
    tp = (res.groupby("complaint_type")
             .agg(cases=("unique_key", "count"), med_h=("resolve_h", "median"),
                  excess_72h=("resolve_h", lambda s: (s > 72).mean()))
             .sort_values("cases", ascending=False))
    tp["excess_hours_total"] = tp.cases * tp.med_h  # hours spent beyond the median basis -> crude load proxy
    heavy = tp.head(10)

    kpi = json.loads((PROJECT / "outputs" / "kpis.json").read_text())
    n_over = kpi["n_over_72h"]

    scen_a_saved_h = float(pd.read_csv(PROJECT / "outputs" / "seg_types.csv",
                                       index_col=0).head(5)["cases"].sum() * CASE_TEAM_LABOR_H * .12)
    scen_b_cost = n_over * CASE_TEAM_LABOR_H * COST_PER_CASE_HOUR * .35   # clear 35% of sweep cases
    scen = {
        "assumptions": {"staff_cost_per_hour": COST_PER_CASE_HOUR,
                        "labor_hours_per_case": CASE_TEAM_LABOR_H},
        "a_redeploy_hours_saved_per_quarter": round(scen_a_saved_h, 0),
        "a_redeploy_value_per_quarter": round(scen_a_saved_h * COST_PER_CASE_HOUR, 0),
        "b_sla_sweep_target_cases": int(n_over),
        "b_sla_sweep_cost": round(scen_b_cost, 0),
        "b_sla_sweep_backlog_reduction_pct": round(float(.35), 2),
    }
    save_json(scen, PROJECT / "outputs" / "scenarios.json")

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    hh = heavy.head(10).sort_values("med_h")
    ax.barh(hh.index, hh.med_h, color="#134e5e")
    ax2 = ax.twiny()
    ax2.plot(hh.cases, hh.index, "o", color="#e2584c", label="case volume")
    ax.set_xlabel("Median resolution (h)"); ax2.set_xlabel("Cases (volume)", color="#e2584c")
    ax.set_title("Heavy-volume, slow complaint types — the swing capacity")
    save_png(fig, PROJECT / "outputs" / "charts" / "pareto_types.png")
    print(json.dumps(scen, indent=2))


if __name__ == "__main__":
    main()
