"""02-operations-311 — 04_dashboard.py — single-file interactive ops dashboard."""
from pathlib import Path
import json
import sys

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

_shared_root = Path(__file__).resolve().parent
while _shared_root != _shared_root.parent and not (_shared_root / "shared").is_dir():
    _shared_root = _shared_root.parent
sys.path.insert(0, str(_shared_root))  # callable from repo root or standalone checkout
from shared.dashboard import build_dashboard   # noqa: E402

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "outputs"

DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def main() -> None:
    kpis = json.loads((OUT / "kpis.json").read_text())
    scen = json.loads((OUT / "scenarios.json").read_text())
    ag = pd.read_csv(OUT / "seg_agency.csv", index_col=0)
    tp = pd.read_csv(OUT / "seg_types.csv", index_col=0)
    bo = pd.read_csv(OUT / "seg_borough.csv", index_col=0)
    heat = pd.read_csv(OUT / "seg_dowhour.csv", index_col=0)

    fig_ag = go.Figure(go.Bar(y=ag.sort_values("med_h").tail(10).index,
                              x=ag.sort_values("med_h").tail(10).med_h, orientation="h",
                              marker_color="#134e5e",
                              text=ag.sort_values("med_h").tail(10).med_h.round(0).astype(int),
                              textposition="outside"))
    fig_ag.update_layout(xaxis_title="Median resolution (hours)", yaxis=dict(title=""))

    fig_tp = px.scatter(x=tp.cases, y=tp.med_h, text=tp.index, log_x=True,
                        size=(tp.cases / tp.cases.max() * 550 + 40),
                        color=tp.over_72h, color_continuous_scale="Viridis")
    fig_tp.update_layout(xaxis_title="Cases (log)", yaxis_title="Median hours",
                         yaxis_type="log", coloraxis_colorbar=dict(title=">72h share"))
    fig_tp.update_traces(textfont_size=9, textposition="top center")

    fig_bo = go.Figure()
    fig_bo.add_trace(go.Bar(y=list(bo.index), x=bo.med_h, orientation="h",
                            marker_color="#0e7490", name="Median hours"))
    fig_bo.update_layout(yaxis=dict(title=""))

    fig_heat = go.Figure(go.Heatmap(z=heat.values, x=list(heat.columns), y=[DOW[int(d)] for d in heat.index],
                                    colorscale="Tealgrn"))
    fig_heat.update_layout(xaxis_title="Hour of day", yaxis_title="Day of week")

    build_dashboard(
        str(PROJECT / "dashboard" / "index.html"),
        title="Civic Service Operations — 311 Efficiency Readout",
        subtitle=("Where does service delivery lose time, and which capacity fix pays for itself? "
                  "Built from 311 requests opened June–Aug 2026 (public NYC Open Data)."),
        badges=["Operations", "Backlog analytics", "Capacity scenarios", "LLM narration"],
        kpis=[
            {"label": "Cases in quarter", "value": f"{kpis['cases']:,}"},
            {"label": "Still open (backlog)", "value": f"{kpis['backlog_pct']:.0%}"},
            {"label": "Median resolution", "value": f"{kpis['median_resolve_h']:.0f}h", "note": "P90: %.0fh" % kpis['p90_resolve_h']},
            {"label": "Closed >72h", "value": f"{kpis['share_over_72h']:.0%}", "note": f"{kpis['n_over_72h']:,} cases"},
            {"label": "Scenario A value", "value": f"${scen['a_redeploy_value_per_quarter']:,.0f}", "note": "/quarter"},
        ],
        figures=[
            {"title": "Slowest agencies", "sub": "min 500 closed cases in the quarter", "fig": fig_ag},
            {"title": "Complaint type economics", "sub": "volume vs resolution time vs SLA-miss share", "fig": fig_tp},
            {"title": "Borough load", "fig": fig_bo},
            {"title": "Arrival heatmap", "sub": "when complaints arrive — staff to the curve", "fig": fig_heat},
        ],
        recommendations=[
            "Re-deploy ~12% of day-shift capacity onto the 5 slowest heavy-volume complaint types "
            f"→ {scen['a_redeploy_hours_saved_per_quarter']:,.0f} staff-hours/quarter saved "
            f"(≈${scen['a_redeploy_value_per_quarter']:,.0f}).",
            "Run an SLA sweep on the >72h queue (35% target) for "
            f"${scen['b_sla_sweep_cost']:,.0f} — visible closure-rate win for council reporting.",
            "Shift intake staffing toward the evening arrival peak seen on the heatmap.",
            "Introduce a per-agency SLA dashboard with weekly exception review of the worst 10 types.",
        ],
        footer=("Data: NYC 311 via Socrata open-data API (public). AI narrates verified metrics only. "
                "Stated assumptions: $45/staff-hour, 1.6 labor-hours per case."),
    )
    print("dashboard written")


if __name__ == "__main__":
    main()
