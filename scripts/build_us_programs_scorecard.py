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
CIP_FIELDS: dict[str, list[str]] = {
    "1101": ["computing"],  # Computer and Information Sciences, General
    "1104": ["computing"],  # Information Science/Studies
    "1107": ["computing"],  # Computer Science
    "1109": ["computing"],  # Computer Systems Networking and Telecommunications
    "1409": ["computing", "electrical_electronic"],  # Computer Engineering
    "1410": ["electrical_electronic"],  # Electrical, Electronics, and Communications Engineering
    "1447": ["electrical_electronic", "computing"],  # Electrical and Computer Engineering
    "1419": ["mechanical"],  # Mechanical Engineering
    "1441": ["mechanical", "electrical_electronic"],  # Electromechanical Engineering
    "1442": ["mechanical", "electrical_electronic"],  # Mechatronics, Robotics, and Automation
    "1407": ["chemical_materials"],  # Chemical Engineering
    "1443": ["chemical_materials"],  # Biochemical Engineering
    "1406": ["chemical_materials"],  # Ceramic Sciences and Engineering
    "1418": ["chemical_materials"],  # Materials Engineering
    "1420": ["chemical_materials"],  # Metallurgical Engineering
    "1432": ["chemical_materials"],  # Polymer/Plastics Engineering
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
