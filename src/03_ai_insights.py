"""02-operations-311 — 03_ai_insights.py — measured AI narrative over verified metrics."""
from pathlib import Path
import json
import sys

_shared_root = Path(__file__).resolve().parent
while _shared_root != _shared_root.parent and not (_shared_root / "shared").is_dir():
    _shared_root = _shared_root.parent
sys.path.insert(0, str(_shared_root))  # callable from repo root or standalone checkout
from shared import llm   # noqa: E402

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "outputs"


def main() -> None:
    kpis = json.loads((OUT / "kpis.json").read_text())
    scen = json.loads((OUT / "scenarios.json").read_text())
    drivers = {
        "Backlog is concentrated, not universal": (
            f"{kpis['backlog_pct']:.0%} of ~{kpis['cases']:,} cases in the quarter were still open; "
            f"{kpis['share_over_72h']:.0%} of closed cases missed a 72h service bar."),
        "Agency-level scatter": (
            f"Slowest heavy-volume agency: {kpis['worst_agency']} (median {kpis['worst_agency_med_h']:.0f}h) "
            f"vs best {kpis['best_agency']} at {kpis['best_agency_med_h']:.0f}h."),
        "Arrivals curve": ("Complaint arrivals spike in the evening — intake shift design, not headcount, "
                           "is the near-term fix."),
        "Scenario economics": (f"A) redeploying ~12% of intake capacity to the 5 slowest heavy types frees "
                               f"${scen['a_redeploy_value_per_quarter']:,.0f} of staff-hours per quarter; "
                               f"B) an SLA sweep clearing 35% of the >72h queue costs "
                               f"${scen['b_sla_sweep_cost']:,.0f}."),
    }
    llm_prompt = f"""You are briefing a city-operations deputy commissioner. Use ONLY verified metrics.
Deliver: (1) two-sentence executive read, (2) ranked 90-day actions, (3) what to measure
next quarter. Metrics: {json.dumps({**kpis, **scen}, indent=1)}"""
    md = llm.write_insights(str(OUT / "insights.md"), "Civic service operations readout",
                            kpis, drivers, llm_prompt)
    print(md[:1200])


if __name__ == "__main__":
    main()
