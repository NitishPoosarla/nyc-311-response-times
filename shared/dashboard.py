"""Reusable single-file HTML dashboard builder (no server, no build step).

Each project's `04_dashboard.py` calls build_dashboard(...) with
KPI cards, plotly figures, tables and recommendations. The output is one
self-contained `dashboard.html` (plotly.js loaded from CDN) that:
  - can be opened locally by double-clicking,
  - deploys free on GitHub Pages,
  - looks professional in a portfolio README / LinkedIn post.
"""
from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go

PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"

_CSS = """
:root{--ink:#0f172a;--muted:#64748b;--brand:#0e7490;--bg:#f6f8fa;--card:#fff;--line:#e2e8f0}
*{box-sizing:border-box}
body{margin:0;font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--ink)}
header{background:linear-gradient(120deg,#0f172a,#134e5e 75%,#1b8a5a);color:#fff;padding:36px 40px 30px}
header h1{margin:0 0 6px;font-size:28px;letter-spacing:-.5px}
header p{margin:0;color:#cbd5e1;max-width:900px;font-size:15px;line-height:1.5}
.badge{display:inline-block;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.25);
border-radius:999px;padding:4px 12px;font-size:12px;margin:10px 8px 0 0}
main{max-width:1280px;margin:0 auto;padding:28px 24px 48px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin:0 0 8px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px}
.kpi .label{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em}
.kpi .value{font-size:26px;font-weight:700;margin-top:4px}
.kpi .note{color:var(--muted);font-size:12px;margin-top:4px}
section.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;
padding:20px;margin-top:18px;box-shadow:0 1px 2px rgba(15,23,42,.04)}
section.panel h2{margin:0 0 12px;font-size:17px}
.panel .sub{color:var(--muted);font-size:13px;margin:-8px 0 12px}
.reco{border-left:4px solid var(--brand);background:#f0fdfa;padding:12px 16px;border-radius:0 10px 10px 0;margin-top:10px}
.reco b{color:#0f766e}
table.data{border-collapse:collapse;width:100%;font-size:13px}
table.data th{background:#f1f5f9;text-align:left;padding:8px 10px;border-bottom:2px solid var(--line)}
table.data td{padding:8px 10px;border-bottom:1px solid var(--line)}
table.data tr:hover td{background:#f8fafc}
footer{color:var(--muted);font-size:12px;padding:18px 40px 30px;max-width:1280px;margin:0 auto}
.btn{position:fixed;right:18px;bottom:18px;background:var(--ink);color:#fff;border:none;border-radius:999px;
padding:10px 18px;cursor:pointer;font-size:13px;box-shadow:0 4px 14px rgba(0,0,0,.2)}
@media print{.btn{display:none}body{background:#fff}}
"""

_JS_PRINT = """
function printDash(){window.print();}
"""


def _fig_html(fig: go.Figure, height: int = 380) -> str:
    fig.update_layout(
        height=height,
        margin={"l": 50, "r": 24, "t": 12, "b": 40},
        font={"family": "Segoe UI, system-ui, sans-serif", "size": 12},
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"displayModeBar": False, "responsive": True})


def _png_html(path: str) -> str:
    data = base64.b64encode(Path(path).read_bytes()).decode()
    return f'<img style="max-width:100%;border-radius:8px" src="data:image/png;base64,{data}"/>'


def _table_html(df: pd.DataFrame) -> str:
    return df.to_html(index=False, classes="data", border=0, escape=False)


def build_dashboard(out_path: str, title: str, subtitle: str, badges: list[str],
                    kpis: list[dict[str, str]], figures: list[dict[str, Any]],
                    recommendations: list[str], footer: str, author: str = "") -> str:
    """figures: [{title, sub?, fig|png|table}] - plotly Figure | png path | DataFrame."""
    kpi_html = "".join(
        f'<div class="kpi"><div class="label">{k["label"]}</div>'
        f'<div class="value">{k["value"]}</div>'
        f'<div class="note">{k.get("note", "")}</div></div>'
        for k in kpis
    )
    badges_html = "".join(f'<span class="badge">{b}</span>' for b in badges)
    panels = []
    for f in figures:
        if f.get("fig") is not None:
            body = _fig_html(f["fig"])
        elif f.get("png") is not None:
            body = _png_html(f["png"])
        else:
            body = _table_html(f["table"])
        panels.append(
            f'<section class="panel"><h2>{f["title"]}</h2>'
            + (f'<p class="sub">{f["sub"]}</p>' if f.get("sub") else "")
            + body + "</section>"
        )
    recos = "".join(f'<div class="reco">▸ {r}</div>' for r in recommendations)
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title}</title>
<script src="{PLOTLY_CDN}" charset="utf-8"></script>
<style>{_CSS}</style></head>
<body>
<header>
  <h1>{title}</h1>
  <p>{subtitle}</p>
  <div>{badges_html}</div>
</header>
<main>
  <div class="kpis">{kpi_html}</div>
  {''.join(panels)}
  <section class="panel"><h2>Recommendations</h2>{recos}</section>
</main>
<button class="btn" onclick="printDash()">Export PDF ⤓</button>
<script>{_JS_PRINT}</script>
<footer>
  {footer}{'<br/>Author: ' + author if author else ''}
</footer>
</body></html>"""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(html, encoding="utf-8")
    return out_path
