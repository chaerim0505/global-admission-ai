"""Build US institution facts (official URL, admission rate, SAT range, tuition, difficulty percentile).

Input : data/raw/scorecard/Most-Recent-Cohorts-Institution.csv
        ("Most Recent Institution-Level Data" from https://collegescorecard.ed.gov/data/)
        data/catalogue/us_engineering_programs_scorecard.json (to keep only engineering institutions)
Output: data/catalogue/us_institutions_scorecard.json

difficultyPercentile (0-100, higher = harder to enter) is the within-US percentile of
admission rate (lower rate = harder), averaged with the SAT-average percentile when present.
It is a public-indicator estimate, not an admission prediction (SPEC F08).
Tuition is the published out-of-state undergraduate tuition and fees; graduate tuition
is not in College Scorecard and stays unknown.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "scorecard" / "Most-Recent-Cohorts-Institution.csv"
PROGRAMS = ROOT / "data" / "catalogue" / "us_engineering_programs_scorecard.json"
OUT = ROOT / "data" / "catalogue" / "us_institutions_scorecard.json"


def num(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def percentiles(values: dict[str, float], higher_is_harder: bool) -> dict[str, float]:
    ordered = sorted(values, key=lambda k: values[k], reverse=not higher_is_harder)
    n = len(ordered)
    return {k: round(100 * i / (n - 1), 1) if n > 1 else 50.0 for i, k in enumerate(ordered)}


def main() -> int:
    unitids = {p["unitId"] for p in json.loads(PROGRAMS.read_text(encoding="utf-8"))["programs"]}
    rows = {}
    with SRC.open(newline="", encoding="utf-8", errors="replace") as handle:
        for row in csv.DictReader(handle):
            if row["UNITID"] in unitids:
                rows[row["UNITID"]] = row
    adm = {k: v for k, r in rows.items() if (v := num(r["ADM_RATE"])) is not None}
    sat = {k: v for k, r in rows.items() if (v := num(r["SAT_AVG"])) is not None}
    adm_pct = percentiles(adm, higher_is_harder=False)  # lower admission rate = harder
    sat_pct = percentiles(sat, higher_is_harder=True)
    out = []
    for unitid, r in sorted(rows.items(), key=lambda kv: kv[1]["INSTNM"]):
        parts = [p for p in (adm_pct.get(unitid), sat_pct.get(unitid)) if p is not None]
        url = (r["INSTURL"] or "").strip().rstrip("/")
        out.append({
            "unitId": unitid,
            "universityName": r["INSTNM"].strip(),
            "officialUrl": f"https://{url}" if url and not url.startswith("http") else url or None,
            "admissionRate": adm.get(unitid),
            "satAverage": sat.get(unitid),
            "satMath25_75": [num(r["SATMT25"]), num(r["SATMT75"])],
            "satReading25_75": [num(r["SATVR25"]), num(r["SATVR75"])],
            "undergradTuitionOutOfStateUSD": num(r["TUITIONFEE_OUT"]),
            "difficultyPercentile": round(sum(parts) / len(parts), 1) if parts else None,
            "difficultyBasis": [b for b, p in (("admission_rate", adm_pct.get(unitid)), ("sat_average", sat_pct.get(unitid))) if p is not None],
            "source": "College Scorecard, Most Recent Institution-Level Data",
            "sourceUrl": f"https://collegescorecard.ed.gov/school/?{unitid}",
        })
    OUT.write_text(json.dumps({"source": "https://collegescorecard.ed.gov/data/", "institutions": out}, ensure_ascii=False, indent=1), encoding="utf-8")
    with_index = sum(1 for i in out if i["difficultyPercentile"] is not None)
    with_fee = sum(1 for i in out if i["undergradTuitionOutOfStateUSD"])
    print(f"Saved {len(out)} institutions ({with_index} with difficulty, {with_fee} with tuition) to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
