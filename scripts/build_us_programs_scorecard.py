"""Build a US engineering programme list from the College Scorecard Field of Study file.

Input : data/raw/scorecard/Most-Recent-Cohorts-Field-of-Study.csv
        (download "Most Recent Data by Field of Study" from https://collegescorecard.ed.gov/data/)
Output: data/catalogue/us_engineering_programs_scorecard.json

Each row is one institution x CIP code x credential level. CIP is the federal
classification of the field, so the programme name is the CIP title, not the
university's own programme name. Records stay verificationStatus "needs_check"
until admission requirements are taken from the official programme page.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "scorecard" / "Most-Recent-Cohorts-Field-of-Study.csv"
OUT = ROOT / "data" / "catalogue" / "us_engineering_programs_scorecard.json"

# CIP 4-digit code -> our engineering fields
C, E, M, CH = ["computing"], ["electrical_electronic"], ["mechanical"], ["chemical_materials"]
CV, IS, AE, BM, OT = ["civil_environmental"], ["industrial_systems"], ["aerospace"], ["biomedical"], ["other_engineering"]
# CIP 4-digit code -> SPEC 3.2 engineering fields (all of CIP 14 + core computing in CIP 11)
CIP_FIELDS: dict[str, list[str]] = {
    "1101": C, "1104": C, "1107": C, "1109": C,
    "1401": OT, "1402": AE, "1403": OT, "1404": CV, "1405": BM, "1406": CH, "1407": CH,
    "1408": CV, "1409": ["computing", "electrical_electronic"], "1410": E, "1411": M,
    "1412": OT, "1413": OT, "1414": CV, "1418": CH, "1419": M, "1420": CH, "1421": OT,
    "1422": OT, "1423": OT, "1424": OT, "1425": OT, "1427": IS, "1428": OT, "1432": CH,
    "1433": CV, "1434": OT, "1435": IS, "1436": IS, "1437": IS, "1438": CV, "1439": OT,
    "1440": OT, "1441": ["mechanical", "electrical_electronic"],
    "1442": ["mechanical", "electrical_electronic"], "1443": CH, "1444": CH, "1445": BM,
    "1447": ["electrical_electronic", "computing"], "1448": OT, "1499": OT,
}
DEGREES = {"3": "bachelor", "5": "master", "6": "doctoral"}


def build_records(rows) -> list[dict]:
    records: dict[str, dict] = {}
    for row in rows:
        cip = row["CIPCODE"].strip()
        level = row["CREDLEV"].strip()
        if cip not in CIP_FIELDS or level not in DEGREES or row["MAIN"].strip() != "1":
            continue
        unitid = row["UNITID"].strip()
        if not unitid.isdigit():  # foreign institutions in the file have no US UNITID
            continue
        program_id = f"us_sc_{unitid}_{cip}_{DEGREES[level]}"
        records[program_id] = {
            "programId": program_id,
            "universityName": row["INSTNM"].strip(),
            "unitId": unitid,
            "country": "US",
            "programName": row["CIPDESC"].strip().rstrip("."),
            "cipCode": f"{cip[:2]}.{cip[2:]}",
            "degreeLevel": DEGREES[level],
            "engineeringFields": CIP_FIELDS[cip],
            "source": "College Scorecard, Most Recent Cohorts Field of Study",
            "sourceUrl": f"https://collegescorecard.ed.gov/school/?{unitid}",
            "verificationStatus": "needs_check",
        }
    return sorted(records.values(), key=lambda r: (r["universityName"], r["cipCode"], r["degreeLevel"]))


def main() -> int:
    if not SRC.exists():
        print(f"Missing {SRC}. Download the Field of Study file first.")
        return 1
    with SRC.open(newline="", encoding="utf-8", errors="replace") as handle:
        records = build_records(csv.DictReader(handle))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "source": "https://collegescorecard.ed.gov/data/",
        "file": SRC.name,
        "note": "Programme names are federal CIP titles. Requirements must come from official programme pages.",
        "programs": records,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Saved {len(records)} programmes from {len({r['unitId'] for r in records})} institutions to {OUT}")
    print(Counter((f, r["degreeLevel"]) for r in records for f in r["engineeringFields"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
