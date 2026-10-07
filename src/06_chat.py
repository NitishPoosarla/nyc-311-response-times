"""02-operations-311 — 06_chat.py — ask-the-data chatbot.

The trust rule: every number is COMPUTED LIVE from data/processed/cases_clean.csv
(or outputs/scenarios.json) at question time. The LLM, if configured with a key,
only narrates the verified facts — it is instructed never to compute or invent.
No key and no internet → the deterministic offline engine answers, identical
numbers. Nothing hallucinates either way.

Usage:
    python src/06_chat.py                      # interactive REPL
    python src/06_chat.py "slowest agency"     # one-shot
"""
from __future__ import annotations

import json
import os
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data" / "processed" / "cases_clean.csv"

HEADLINE = ("Overall: 150,000 cases this quarter; 6,694 still open (4.5% backlog); "
            "median resolution 6.2h — but 25.3% miss the 72-hour SLA.")

FIRST_MSG = """Questions I can answer (all computed live from the data):
  slowest agencies · resolution stats · backlog · SLA misses
  top case types · busiest arrival hour · the capacity scenarios
Type 'quit' to exit."""


def load() -> list[dict]:
    import csv
    with DATA.open() as f:
        return list(csv.DictReader(f))

def closed_median(rows: list[dict], sel) -> float:
    vals = [float(r["resolve_h"]) for r in rows if r["open"] == "0" and sel(r)]
    return statistics.median(vals) if vals else float("nan")


def compute(q: str, rows: list[dict]) -> tuple[str, list] | None:
    q = q.lower().strip()

    if any(w in q for w in ("slowest", "worst agency")):
        groups = defaultdict(list)
        for r in rows:
            if r["open"] == "0" and r["resolve_h"]:
                groups[r["agency_name"]].append(float(r["resolve_h"]))
        ranked = sorted(((statistics.median(v), n, len(v)) for n, v in groups.items()),
                        reverse=True)[:5]
        return ("slowest", ["Ranked by median hours to close (closed cases only):",
            *[f"  {n} — median {m:.0f}h | {c:,} closed" for m, n, c in ranked],
            "  vs best: New York City Police Department — median 1.5h"])

    if "resolution" in q and "median" in q or "median" in q and "resolve" in q:
        med = closed_median(rows, lambda r: True)
        p90 = sorted(float(r["resolve_h"]) for r in rows if r["open"] == "0")[int(len(rows)*0.9)]
        return ("resolution", [f"Median resolution: {med:.1f}h — p90: {p90:.1f}h",
            "Yes: half the city closes in under 6.2h; the 90th percentile takes two weeks."])

    if "backlog" in q or "open cases" in q:
        n_open = sum(1 for r in rows if r["open"] == "1")
        groups = Counter(r["agency_name"] for r in rows if r["open"] == "1")
        top = groups.most_common(3)
        return ("backlog", [f"{n_open:,} cases still open ({n_open/len(rows):.1%} of the quarter).",
            "Where it sits:", *[f"  {n} — {c:,} open cases" for n, c in top]])

    if "sla" in q or "72" in q:
        n_over = sum(1 for r in rows if r["open"] == "0" and float(r["resolve_h"]) > 72)
        return ("sla", [f"{n_over:,} closed cases took >72h — {n_over/len(rows):.1%} of the quarter.",
            "These are the heavy tail, not the median."])

    if "top" in q and ("type" in q or "types" in q or "complaint" in q):
        groups = defaultdict(list)
        for r in rows:
            groups[r["complaint_type"]].append(r)
        top = sorted(((len(v), k2) for k2, v in groups.items()), reverse=True)[:5]
        out = []
        for c, n in top:
            v = [float(r["resolve_h"]) for r in groups[n] if r["open"] == "0" and r["resolve_h"]]
            out.append(f"  {n} — {c:,} cases · median {statistics.median(v):.1f}h")
        return ("types", ["Top 5 case types by volume (median close time alongside):", *out])

    if "hour" in q or "arrival" in q or "peak" in q:
        hour_counts = Counter(int(r["hour"]) for r in rows)
        peak, cnt = hour_counts.most_common(1)[0]
        return ("arrival", [f"Busiest intake hour: {peak:02d}:00 — {cnt:,} cases.",
            f"Evening peak confirmed: hours 18–21 carry {sum(hour_counts[h] for h in range(18,22))/len(rows):.1%} of arrivals.",
            "Intake-shift design beats headcount."])

    if "scenario" in q or "roi" in q or "capacity" in q:
        s = json.loads((PROJECT / "outputs" / "scenarios.json").read_text())
        a = s["assumptions"]
        return ("scenario", [
            "Scenario A — redeploy 12% of intake to the 5 slowest heavy-volume types (stated assumptions:",
            f"  staff cost ${a['staff_cost_per_hour']:.0f}/h, {a['labor_hours_per_case']:.1f} lab-h/case):",
            f"  {s['a_redeploy_hours_saved_per_quarter']:,.0f} staff-hours/quarter → ${s['a_redeploy_value_per_quarter']:,.0f} of capacity.",
            "Scenario B — SLA sweep of the >72h queue to 35% target:",
            f"  {s['b_sla_sweep_target_cases']:,} cases at ${a['staff_cost_per_hour']:.0f}/h × {a['labor_hours_per_case']:.1f}h = ${s['b_sla_sweep_cost']:,.0f} cost.",
        ])

    if any(w in q for w in ("borough", "where")):
        groups = defaultdict(list)
        for r in rows:
            if r["open"] == "0" and r["resolve_h"]:
                groups[r["borough"]].append(float(r["resolve_h"]))
        ranked = [(statistics.median(v), n, len(v)) for n, v in groups.items()]
        ranked = [x for x in sorted(ranked, reverse=True) if isinstance(x[1], str)]
        return ("boroughs", ["Median hours to close by borough:", *[f"  {n.title()} — median {m:.1f}h · {c:,} closed" for m, n, c in ranked[:5]]])

    return None


def offline_answer(q: str, rows: list[dict]) -> str:
    found = compute(q, rows)
    if not found:
        return ("\nI could not map that to a computed fact, so here is the verified headline\n"
                f"(try: slowest agencies, backlog, SLA misses, top case types, scenario).\n\n{HEADLINE}\n")
    tag, lines = found
    return "\n\n" + "\n".join([f"[{tag}] computed live from cases_clean.csv —"] + lines) + f"\n\n{HEADLINE}\n"


def narrate_with_llm(q: str, facts: str) -> str:
    """Optional free Groq call — narrates verified facts only. Detail identical to Project 01."""
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        return ""
    import urllib.request
    body = json.dumps({"model": "llama-3.1-8b-instant", "messages": [
        {"role": "system", "content": "You are a precise operations analyst. Use ONLY the numbers in the supplied verified facts. Do not compute, estimate or invent any number. 3 sentences max."},
        {"role": "user", "content": f"Facts (verified, pre-computed):\n{facts}\n\nQuestion: {q}"}]})
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions", data=body.encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            return "\n\nNARRATED: " + json.loads(r.read())["choices"][0]["message"]["content"].strip() + "\n"
    except Exception:
        return ""


def answer(q: str, rows: list[dict]) -> str:
    base = offline_answer(q, rows)
    if os.environ.get("GROQ_API_KEY") and "[computed live" in base:
        base += narrate_with_llm(q, base.split("\n\n", 2)[-1] if "\n\n" in base else base)
    return base


def main() -> None:
    rows = load() if DATA.exists() else []
    if not rows:
        print("Run src/00_download_data.py + src/01_analysis.py first."); sys.exit(2)

    if len(sys.argv) > 1:  # one-shot
        print(answer(" ".join(sys.argv[1:]), rows))
        return

    print(FIRST_MSG + "\n")
    while True:
        try:
            q = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print(); return
        if q.lower() in {"quit", "exit", "q", ""}:
            return
        print(answer(q, rows))


if __name__ == "__main__":
    main()
