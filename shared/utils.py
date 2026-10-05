"""Shared utilities: dataset download with cache, chart styling, JSON export."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

PORTFOLIO_ROOT = Path(__file__).resolve().parents[1]

_MPL_READY = False


def mpl_setup() -> None:
    """Consistent, presentation-quality matplotlib defaults."""
    global _MPL_READY
    if _MPL_READY:
        return
    matplotlib.use("Agg")
    plt.rcParams.update({
        "figure.dpi": 110,
        "savefig.dpi": 150,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": .25,
        "axes.titleweight": "semibold",
        "font.size": 10.5,
        "axes.titlesize": 12,
        "figure.facecolor": "white",
    })
    _MPL_READY = True


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def project_dir() -> Path:
    """Directory of the script that is running (assumed = project folder)."""
    return Path(sys.argv[0]).resolve().parent.parent


def pdir(path: str | Path = "") -> Path:
    d = Path(path)
    return d


def save_json(obj: object, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, default=str)
    return p


def save_png(fig: plt.Figure, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    return p


# ---------------------------------------------------------------------------
# Downloading datasets (cached)
# ---------------------------------------------------------------------------

def download(url: str, dest: str | Path, desc: str = "") -> Path:
    """Download a URL to a local path, skipping if the file already exists."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"[cache] {desc or url} -> {dest.name} ({dest.stat().st_size:,} bytes)")
        return dest
    print(f"[GET ] {desc or url} ...")
    r = requests.get(url, timeout=180, headers={"User-Agent": "portfolio/1.0"})
    r.raise_for_status()
    dest.write_bytes(r.content)
    print(f"[save] {dest} ({len(r.content):,} bytes)")
    return dest


def unzip(src: str | Path, dest_dir: str | Path) -> list[Path]:
    import zipfile
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    members = []
    with zipfile.ZipFile(src) as z:
        for name in z.namelist():
            target = dest_dir / Path(name).name
            if not target.exists():
                with open(target, "wb") as f:
                    f.write(z.read(name))
            members.append(target)
    return members


# ---------------------------------------------------------------------------
# Quick pipeline helper: add a project root to sys.path so shared imports work
# ---------------------------------------------------------------------------

def bootstrap(project_file: str, depth: int = 2) -> Path:
    """Add portfolio root to sys.path when a project script is run directly."""
    root = Path(project_file).resolve().parents[depth]  # project/src/script.py -> portfolio root
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root
