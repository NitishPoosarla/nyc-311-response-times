"""02 — banner: cream report cover, ops facts, hour-gap strip."""
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

k = json.loads((Path(__file__).resolve().parents[1] / "outputs" / "kpis.json").read_text())

fig, ax = plt.subplots(figsize=(12, 6.75), dpi=100)
ax.set_xlim(0, 12); ax.set_ylim(0, 6.75); ax.axis("off")
fig.patch.set_facecolor("#f6f1e7")

ax.add_patch(plt.Rectangle((0, 6.2), 12, 0.55, color="#2e4057"))
ax.text(0.5, 6.38, "NYC 311 · WHERE AGENCY SPEED DIVERGES 500X", fontsize=12.5,
        fontweight="bold", color="white", va="center")

ax.text(0.5, 4.55, "Where the\nservice time\nactually goes", fontsize=29,
        fontweight="bold", color="#20242a", linespacing=1.15, va="center")
ax.text(0.5, 2.6, f"{k['cases']:,} cases · Jun–Aug · Socrata public data",
        fontsize=11, color="#5a6673")

stats = [
    (f"{k['median_resolve_h']:.1f} h", "citywide median resolution", 5.35),
    (f"{k['p90_resolve_h']:.0f} h", "p90 — the tail is the program", 4.25),
    (f"{k['share_over_72h']:.1%}", "blow past the 72-hour SLA", 3.15),
    ("725 h vs 1.5 h", "slowest vs fastest agency median", 2.05),
]
for big, small, y in stats:
    ax.text(6.6, y, big, fontsize=16.5, fontweight="bold", color="#2e4057", va="center")
    ax.text(9.35, y, small, fontsize=10, color="#5a6673", va="center")
    ax.plot([6.45, 11.8], [y - 0.55] * 2, color="#d9d0bd", lw=1)

ax.text(0.5, 1.55, "Scenario A redeploys ~12% of intake hours", fontsize=11.5, color="#33383d")
ax.text(0.5, 1.15, "to the five slowest heavy-volume request types;", fontsize=11.5, color="#33383d")
ax.text(0.5, 0.75, "arrival heatmap says intake timing, not headcount.", fontsize=11, color="#8a7f68")
fig.savefig(Path(__file__).resolve().parents[1] / "outputs" / "banner.png",
            dpi=100, facecolor=fig.get_facecolor())
print("banner written")
