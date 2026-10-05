"""02-operations-311 — pull NYC 311 service requests via the Socrata open-data API.

Scope: complaints opened in June–August 2026, key operational fields only.
Source: https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9
"""
from pathlib import Path

import requests

PROJECT = Path(__file__).resolve().parent.parent
BASE = "https://data.cityofnewyork.us/resource/erm2-nwe9.csv"
SELECT = ("unique_key,created_date,closed_date,agency_name,complaint_type,descriptor,"
          "borough,city,agency")
WHERE = "created_date >= '2026-06-01T00:00:00' AND created_date < '2026-09-01T00:00:00'"
PARAMS = {"$select": SELECT, "$where": WHERE, "$limit": "150000", "$order": "created_date"}


def main() -> None:
    dest = PROJECT / "data" / "raw" / "nyc311_2026Q3.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"[cache] {dest.name} present ({dest.stat().st_size:,} bytes)")
        return
    print(f"[GET ] {BASE} ... (150k-row cap, June-Aug 2026)")
    r = requests.get(BASE, params=PARAMS, timeout=300, headers={"User-Agent": "portfolio/1.0"})
    r.raise_for_status()
    dest.write_text(r.text, encoding="utf-8")
    print(f"[save] {dest} ({len(r.content):,} chars)")


if __name__ == "__main__":
    main()
