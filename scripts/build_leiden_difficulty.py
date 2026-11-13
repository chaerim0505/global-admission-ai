"""Compute a within-country difficulty percentile from the Leiden Ranking Open Edition.

Input : data/raw/leiden/leiden_results_5countries.csv (scripts/extract_leiden_results.py)
Output: data/catalogue/leiden_difficulty.json

Uses the Leiden defaults: period 2021-2024, core publications only, fractional counting,
field "Physical sciences and engineering". The index is the within-country percentile of
P_top_10 (number of top-10% cited engineering/physical-science papers). Compared on
2026-11-14 with an average of P_top_10 and PP_top_10: the share-based variant ranked small
or citation-concentrated universities above national flagships (e.g. Sejong above SNU,
Galway above Trinity College Dublin), so the volume indicator was chosen
(see docs/ARCHITECTURE.md). Higher = more selective research university. It is a public-indicator estimate, not an admission prediction (SPEC F08).
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "leiden" / "leiden_results_5countries.csv"
OUT = ROOT / "data" / "catalogue" / "leiden_difficulty.json"
PERIOD, FIELD = "2021–2024", "Physical sciences and engineering"
COUNTRY_CODES = {"South Korea": "KR", "United States": "US", "United Kingdom": "GB", "Netherlands": "NL", "Ireland": "IE"}


def percentile(values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(values, key=values.get)
    n = len(ordered)
    return {k: round(100 * i / (n - 1), 1) if n > 1 else 50.0 for i, k in enumerate(ordered)}


def main() -> int:
    by_country: dict[str, list[dict]] = defaultdict(list)
    with SRC.open(encoding="utf-8") as handle:
        for r in csv.DictReader(handle):
            if (r["Period"] == PERIOD and r["Field"] == FIELD and r["Core_pubs_only"] == "1"
                    and r["Frac_counting"] == "1" and r["P_top_10"] and r["PP_top_10"]):
                by_country[COUNTRY_CODES[r["Country"]]].append(r)
    out = []
    for country, rows in by_country.items():
        top = percentile({r["ROR_ID"]: float(r["P_top_10"]) for r in rows})
        for r in rows:
            ror = r["ROR_ID"]
            out.append({
                "universityName": r["University"],
                "rorId": f"https://ror.org/{ror}",
                "country": country,
                "P": round(float(r["P"])),
                "P_top_10": round(float(r["P_top_10"]), 1),
                "PP_top_10": round(float(r["PP_top_10"]), 4),
                "difficultyPercentile": top[ror],
                "difficultyBasis": f"Leiden Ranking Open Edition 2026, {FIELD}, {PERIOD}, within-country percentile of P_top_10",
                "sourceUrl": "https://open.leidenranking.com",
            })
    out.sort(key=lambda x: (x["country"], -x["difficultyPercentile"]))
    OUT.write_text(json.dumps({"source": "CWTS Leiden Ranking Open Edition 2026", "universities": out}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Saved {len(out)} universities to {OUT}")
    for c in by_country:
        print(c, len(by_country[c]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
