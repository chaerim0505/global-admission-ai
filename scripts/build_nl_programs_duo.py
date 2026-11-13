"""Build a Dutch engineering programme list from the DUO HO Opleidingsoverzicht file.

Input : data/raw/duo/ho_opleidingsoverzicht.csv
        (https://onderwijsdata.duo.nl/datasets/ho_opleidingsoverzicht -> ho_opleidingsoverzicht)
Output: data/catalogue/nl_engineering_programs_duo.json

Keeps research-university (WO) bachelor and master programmes that are still
running, classified by ISCED-F field code with an English-name fallback.
Records stay verificationStatus "needs_check" until requirements come from the
official programme page.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "duo" / "ho_opleidingsoverzicht.csv"
OUT = ROOT / "data" / "catalogue" / "nl_engineering_programs_duo.json"
DATASET_URL = "https://onderwijsdata.duo.nl/datasets/ho_opleidingsoverzicht"

ISCED_FIELDS = {
    "0611": ["computing"], "0612": ["computing"], "0613": ["computing"], "0619": ["computing"],
    "0710": ["other_engineering"],
    "0711": ["chemical_materials"],
    "0712": ["civil_environmental"],
    "0713": ["electrical_electronic"],
    "0714": ["electrical_electronic", "computing"],
    "0715": ["mechanical"],
    "0716": ["mechanical"],
    "0719": ["other_engineering"],
    "0722": ["chemical_materials"],
    "0724": ["other_engineering"],
    "0732": ["civil_environmental"],
}
# English-name overrides checked before the ISCED code (ISCED files some programmes elsewhere)
KEYWORDS = [
    ("aerospace", ["aerospace"]), ("biomedical engineering", ["biomedical"]),
    ("materials", ["chemical_materials"]), ("industrial engineering", ["industrial_systems"]),
    ("systems engineering", ["industrial_systems"]),
    ("electrical", ["electrical_electronic"]), ("embedded", ["electrical_electronic", "computing"]),
    ("computer", ["computing"]), ("artificial intelligence", ["computing"]), ("data science", ["computing"]),
    ("software", ["computing"]), ("mechanical", ["mechanical"]), ("robotics", ["mechanical", "electrical_electronic"]),
    ("chemical", ["chemical_materials"]), ("civil", ["civil_environmental"]),
]
LEVELS = {"WO-BA": "bachelor", "WO-MA": "master"}


def fields_for(row: dict) -> list[str]:
    name = english_name(row).lower()
    for word, fields in KEYWORDS:
        if word in name:
            return fields
    return ISCED_FIELDS.get(row["ISCED_RUBRIEK"][:4], [])


def english_name(row: dict) -> str:
    return (row["INTERNATIONALE_NAAM"] or row["EIGENNAAM_ENGELS"] or row["NAAM_LANG"]).strip()


def is_active(row: dict, today: str) -> bool:
    end = row["EINDDATUM"][:10]
    return not end or end > today


def build_records(rows, today: str) -> list[dict]:
    records: dict[str, dict] = {}
    for row in rows:
        if row["SOORT"] != "OPLEIDING" or row["NIVEAU"] not in LEVELS or not is_active(row, today):
            continue
        fields = fields_for(row)
        if not fields:
            continue
        code = row["ERKENDEOPLEIDINGSCODE"] or row["OPLEIDINGSEENHEIDCODE"]
        degree = LEVELS[row["NIVEAU"]]
        program_id = f"nl_duo_{row['ONDERWIJSBESTUURID']}_{code}_{degree}"
        records[program_id] = {
            "programId": program_id,
            "universityName": row["ONDERWIJSBESTUUR_NAAM"].strip(),
            "country": "NL",
            "programName": english_name(row),
            "programNameDutch": row["NAAM_LANG"].strip(),
            "crohoCode": code,
            "iscedCode": row["ISCED_RUBRIEK"][:4] or None,
            "degreeLevel": degree,
            "engineeringFields": fields,
            "source": "DUO HO Opleidingsoverzicht (RIO)",
            "sourceUrl": DATASET_URL,
            "verificationStatus": "needs_check",
        }
    return sorted(records.values(), key=lambda r: (r["universityName"], r["degreeLevel"], r["programName"]))


def main() -> int:
    if not SRC.exists():
        print(f"Missing {SRC}")
        return 1
    with SRC.open(newline="", encoding="utf-8-sig") as handle:
        records = build_records(csv.DictReader(handle), date.today().isoformat())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"source": DATASET_URL, "programs": records}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Saved {len(records)} programmes from {len({r['universityName'] for r in records})} institutions to {OUT}")
    print(Counter((f, r["degreeLevel"]) for r in records for f in r["engineeringFields"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
