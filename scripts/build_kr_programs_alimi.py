"""Build the Korean engineering programme list from data.go.kr standard data.

Input : data/raw/kr_api/univ_major.json  (전국대학별학과정보표준데이터, via scripts/fetch_kr_univ_api.py)
        data/raw/kr_api/univ_info.json   (전국대학및전문대학정보표준데이터)
Output: data/catalogue/kr_engineering_programs_alimi.json

Keeps: broad field 공학, departments that are not closed (폐과 removed),
universities and graduate schools that grant 학사/석사/박사
(4-year universities, 산업대학, 일반대학원, 전문대학원). Junior colleges, cyber
universities and part-time special graduate schools (특수대학원) are left out.
Sub-field comes from the standard classification code with a department-name check.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "kr_api"
OUT = ROOT / "data" / "catalogue" / "kr_engineering_programs_alimi.json"
DATASET = "공공데이터포털 전국대학별학과정보표준데이터 (tn_pubr_public_univ_major_api)"

KEEP_SCHOOL_TYPES = {"대학교", "산업대학", "일반대학원", "전문대학원"}
DEGREES = {"학사": ["bachelor"], "석사": ["master"], "박사": ["doctoral"],
           "석사+박사": ["master", "doctoral"], "석사+박사+석박사통": ["master", "doctoral"],
           "박사+석박사통합": ["doctoral"], "석박사통합": ["doctoral"], "석사+석박사통합": ["master", "doctoral"]}
GENERIC = re.compile(r"자유전공|자율전공|공학계열$|공과대학$|^공학부$|교육")
NAME_RULES = [  # every matching rule adds its fields (max 2), in this order
    (r"의공|의용|바이오메디컬|biomedical|뇌공학|바이오.*공학", ["biomedical"]),
    (r"항공|우주", ["aerospace"]),
    (r"원자력|원자핵|양자공학|조선|해양공학|에너지자원|자원공학", ["other_engineering"]),
    (r"공간정보|측량|지리정보", ["civil_environmental"]),
    (r"반도체|전기|전자|제어", ["electrical_electronic"]),
    (r"컴퓨터|전산|소프트웨어|인공지능|AI|데이터|정보보호|보안|사이버|정보통신|정보공학|SW|통신", ["computing"]),
    (r"기계|메카트로닉스|로봇|자동차|금속|모빌리티", ["mechanical"]),
    (r"화학|화공|고분자|신소재|재료|소재", ["chemical_materials"]),
    (r"토목|건설|도시|환경|건축공학|교통", ["civil_environmental"]),
    (r"산업|시스템|안전|경영공학", ["industrial_systems"]),
]
NON_ENGINEERING = re.compile(r"미디어|경영|디자인|콘텐츠|메타버스|문화|헬스케어|게임")
CODE_FIELDS = {"D15": ["electrical_electronic"], "D16": ["civil_environmental"], "D17": ["industrial_systems"],
               "D18": ["chemical_materials"], "D19": ["mechanical"], "D20": ["chemical_materials"],
               "D26": ["other_engineering"], "D99": ["other_engineering"]}


def base_university(name: str) -> str:
    match = re.match(r"(.+?(대학교|과학기술원|대학원대학교|과학기술대학교))", name)
    return match.group(1) if match else name.split(" ")[0]


def fields_for(row: dict) -> list[str]:
    code = row.get("stdClsfAfilCd", "")[:3]
    name = row.get("scsbjtNm", "")
    if code not in CODE_FIELDS or GENERIC.search(name) or name.strip() in {"건축학과", "건축학부", "건축학전공"}:
        return []
    if NON_ENGINEERING.search(name) and "공학" not in name:
        return []  # media/management/design names filed under engineering codes
    if re.search(r"건축학전공|실내건축|건축학과\(건축학", name):
        return []  # architecture design degrees, not engineering
    matched: list[str] = []
    if re.search(r"공간정보|측량|지리정보", name):
        return ["civil_environmental"]  # geomatics, not computing
    for pattern, fields in NAME_RULES:
        if re.search(pattern, name, re.IGNORECASE):
            matched += [f for f in fields if f not in matched]
    if matched:
        return matched[:2]
    return CODE_FIELDS[code] if "공" in name else []


def main() -> int:
    majors = json.loads((RAW / "univ_major.json").read_text(encoding="utf-8"))
    infos = json.loads((RAW / "univ_info.json").read_text(encoding="utf-8"))
    info_by_name = {}
    for info in infos:
        info_by_name.setdefault(info["schlNm"], info)
    records: dict[str, dict] = {}
    for row in majors:
        if (row.get("univOneslfAfilNm") != "공학" or row.get("scsbjtSttsNm") == "폐과"
                or row.get("schlSeNm") not in KEEP_SCHOOL_TYPES or row.get("degCrseCrsNm") not in DEGREES):
            continue
        fields = fields_for(row)
        if not fields:
            continue
        university = base_university(row["schlNm"])
        info = info_by_name.get(university) or info_by_name.get(row["schlNm"]) or {}
        homepage = (info.get("hmpgAddr") or "").strip()
        if homepage and not homepage.startswith("http"):
            homepage = "https://" + homepage.lstrip("/")
        for degree in DEGREES[row["degCrseCrsNm"]]:
            key = f"{row['schlNm']}|{row['scsbjtNm']}|{degree}"
            program_id = "kr_alimi_" + hashlib.sha1(key.encode()).hexdigest()[:12]
            records[program_id] = {
                "programId": program_id,
                "universityName": university,
                "universityNameEnglish": info.get("schlEngNm") or None,
                "schoolName": row["schlNm"],
                "schoolType": row["schlSeNm"],
                "country": "KR",
                "programName": row["scsbjtNm"],
                "college": row.get("collegeNm") or None,
                "degreeLevel": degree,
                "engineeringFields": fields,
                "classificationCode": row.get("stdClsfAfilCd"),
                "departmentStatus": row.get("scsbjtSttsNm"),
                "admissionQuota": row.get("mtcltnFxnoCnt") or None,
                "dataYear": row.get("yr"),
                "officialUrl": homepage or None,
                "source": DATASET,
                "sourceUrl": homepage or "https://www.academyinfo.go.kr",
                "verificationStatus": "needs_check",
            }
    out = sorted(records.values(), key=lambda r: (r["universityName"], r["degreeLevel"], r["programName"]))
    OUT.write_text(json.dumps({"source": DATASET, "programs": out}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Saved {len(out)} programmes from {len({r['universityName'] for r in out})} universities to {OUT}")
    print(Counter((f, r["degreeLevel"]) for r in out for f in r["engineeringFields"]).most_common())
    return 0


if __name__ == "__main__":
    sys.exit(main())
