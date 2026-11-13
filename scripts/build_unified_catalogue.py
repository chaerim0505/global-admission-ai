"""Merge every country's programme list into one catalogue for the recommender (SPEC 3.0, F08).

Inputs (data/catalogue/): us/kr/nl programme lists, ie/gb official master's lists,
us_institutions_scorecard.json, kr_institutions_alimi.json, leiden_difficulty.json,
university_ror.json, plus the team catalogue data/programs_integrated.json.
Output: data/catalogue/programs_unified.json

Each programme gets: source, officialDomain, difficultyPercentile (+ basis), and
undergraduate tuition where a public figure exists. Degree levels use the app's values
(undergraduate / master / phd). Team records win over dataset records for the same programme.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "data" / "catalogue"
OUT = CAT / "programs_unified.json"
DEGREE = {"bachelor": "undergraduate", "undergraduate": "undergraduate", "master": "master", "doctoral": "phd", "phd": "phd"}
NL_TO_LEIDEN = {
    "Technische Universiteit Delft": "Delft University of Technology",
    "Technische Universiteit Eindhoven": "Eindhoven University of Technology",
    "Rijksuniversiteit Groningen": "University of Groningen",
    "Universiteit Leiden": "Leiden University",
    "Universiteit Utrecht": "Utrecht University",
    "Universiteit Twente": "University of Twente",
    "Universiteit van Amsterdam": "University of Amsterdam",
    "Het College van Bestuur van de Radboud Universiteit Nijmegen": "Radboud University",
    "Wageningen University": "Wageningen University & Research",
    "Het College van Bestuur van de Vrije Universiteit": "Vrije Universiteit Amsterdam",
    "Maastricht University": "Maastricht University",
    "Erasmus Universiteit Rotterdam": "Erasmus University Rotterdam",
    "Open Universiteit Nederland": "Open University of the Netherlands",
    "Stichting Katholieke Universiteit Brabant": "Tilburg University",
}


def load(name: str, key: str):
    return json.loads((CAT / name).read_text(encoding="utf-8"))[key]


def norm(text: str | None) -> str:
    text = unicodedata.normalize("NFKC", text or "").lower()
    text = re.sub(r"\(.*?\)", " ", text).replace("&", " and ").replace("’", "'")
    text = re.sub(r"\b(the|of|campus immersion)\b", " ", text)
    return re.sub(r"[^a-z0-9가-힣]+", "", text)


def domain(url: str | None) -> str | None:
    if not url:
        return None
    host = urlparse(url if "://" in url else "https://" + url).hostname or ""
    return host.removeprefix("www.") or None


def main() -> int:
    leiden = load("leiden_difficulty.json", "universities")
    leiden_by_name = {(u["country"], norm(u["universityName"])): u for u in leiden}
    leiden_by_ror = {u["rorId"]: u for u in leiden}
    ror_by_name = {u["universityName"]: u["rorId"] for u in load("university_ror.json", "universities")}
    us_inst = {i["unitId"]: i for i in load("us_institutions_scorecard.json", "institutions")}
    kr_inst = {}
    for i in load("kr_institutions_alimi.json", "institutions"):
        if i["campusType"] == "본교" or i["universityName"] not in kr_inst:
            kr_inst[i["universityName"]] = i

    def leiden_for(country: str, *names: str, ror: str | None = None):
        if ror and ror in leiden_by_ror:
            return leiden_by_ror[ror]
        for name in names:
            hit = leiden_by_name.get((country, norm(name)))
            if hit:
                return hit
        return None

    programs: dict[tuple, dict] = {}

    def add(p: dict, priority: int) -> None:
        key = (p["country"], norm(p["universityName"]), p["degreeLevel"], norm(p["programName"]))
        if key not in programs or priority > programs[key]["_priority"]:
            programs[key] = {**p, "_priority": priority}

    for p in load("us_engineering_programs_scorecard.json", "programs"):
        inst = us_inst.get(p["unitId"], {})
        fee = inst.get("undergradTuitionOutOfStateUSD") if p["degreeLevel"] == "bachelor" else None
        add({**base(p), "universityName": inst.get("universityName", p["universityName"]), "unitId": p["unitId"],
             "officialDomain": domain(inst.get("officialUrl")),
             "difficultyPercentile": inst.get("difficultyPercentile"),
             "difficultyBasis": "College Scorecard admission rate and SAT average (within US)" if inst.get("difficultyPercentile") is not None else None,
             "tuition": {"amount": fee, "currency": "USD", "period": "year", "basis": "out-of-state undergraduate tuition and fees"} if fee else None}, 1)

    for p in load("kr_engineering_programs_alimi.json", "programs"):
        inst = kr_inst.get(p["universityName"], {})
        hit = leiden_for("KR", p.get("universityNameEnglish") or "")
        fee = inst.get("undergradTuitionKRW") if p["degreeLevel"] == "bachelor" else None
        add({**base(p), "universityNameEnglish": p.get("universityNameEnglish"),
             "officialDomain": domain(p.get("officialUrl")),
             **difficulty(hit),
             "tuition": {"amount": fee, "currency": "KRW", "period": "year", "basis": "average undergraduate tuition (대학알리미)"} if fee else None}, 1)

    for p in load("nl_engineering_programs_duo.json", "programs"):
        hit = leiden_for("NL", NL_TO_LEIDEN.get(p["universityName"], p["universityName"]))
        add({**base(p), "universityNameEnglish": hit["universityName"] if hit else None,
             "officialDomain": None, **difficulty(hit), "tuition": None}, 1)

    for file in ("ie_engineering_masters_official.json", "gb_engineering_masters_official.json"):
        for p in load(file, "programs"):
            hit = leiden_for(p["country"], p["universityName"], ror=ror_by_name.get(p["universityName"]))
            add({**base(p), "officialDomain": domain(p["sourceUrl"]), **difficulty(hit), "tuition": None}, 2)

    kr_by_english = {norm(p.get("universityNameEnglish")): p["universityName"]
                     for p in load("kr_engineering_programs_alimi.json", "programs") if p.get("universityNameEnglish")}
    kr_by_english[norm("KAIST")] = "한국과학기술원"
    team = json.loads((ROOT / "data" / "programs_integrated.json").read_text(encoding="utf-8"))
    for p in team:
        if p["country"] == "KR" and norm(p["universityName"]) in kr_by_english:
            p = {**p, "universityNameEnglish": p["universityName"], "universityName": kr_by_english[norm(p["universityName"])]}
        english = p.get("universityNameEnglish") or p["universityName"]
        hit = leiden_for(p["country"], english, ror=ror_by_name.get(english))
        us = next((i for i in us_inst.values() if norm(i["universityName"]) == norm(p["universityName"])), None) if p["country"] == "US" else None
        add({**p, "degreeLevel": DEGREE[p["degreeLevel"]], "unitId": us and us.get("unitId"),
             "source": "team_verified" if p.get("verificationStatus") == "verified" else "official_dataset",
             "officialDomain": domain(p.get("sourceUrl")),
             **(difficulty(hit) if p["country"] != "US" else {"difficultyPercentile": us and us.get("difficultyPercentile"),
                                                               "difficultyBasis": us and "College Scorecard admission rate and SAT average (within US)"}),
             "tuition": p.get("tuition")}, 3)

    out = []
    for p in programs.values():
        p = {k: v for k, v in p.items() if k != "_priority"}
        p["universityKey"] = p.get("rorId") or f'{p["country"]}:{p.get("unitId") or norm(p["universityName"])}'
        out.append(p)
    out.sort(key=lambda p: (p["country"], p["universityName"], p["degreeLevel"], p["programName"]))
    OUT.write_text(json.dumps({"programs": out}, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"Saved {len(out)} programmes to {OUT}")
    print("by country:", Counter(p["country"] for p in out))
    print("with difficulty:", Counter(p["country"] for p in out if p.get("difficultyPercentile") is not None))
    print("with tuition:", Counter(p["country"] for p in out if p.get("tuition")))
    print("degrees:", Counter(p["degreeLevel"] for p in out))
    return 0


def base(p: dict) -> dict:
    return {
        "programId": p["programId"], "universityName": p["universityName"], "country": p["country"],
        "programName": p["programName"], "degreeLevel": DEGREE[p["degreeLevel"]],
        "engineeringFields": p["engineeringFields"], "source": "official_dataset",
        "sourceUrl": p["sourceUrl"], "verificationStatus": "needs_check",
    }


def difficulty(hit: dict | None) -> dict:
    return {"difficultyPercentile": hit["difficultyPercentile"] if hit else None,
            "difficultyBasis": "Leiden Ranking Open Edition 2026, engineering top-10% papers (within country)" if hit else None,
            "rorId": hit["rorId"] if hit else None}


if __name__ == "__main__":
    sys.exit(main())
