"""Build Korean university facts from the 대학알리미 '대학주요정보' workbook.

Input : data/raw/kr_alimi/대학주요정보.xlsx (academyinfo.go.kr 대학주요정보 한눈에 보기 → 엑셀 다운로드)
Output: data/catalogue/kr_institutions_alimi.json

Keeps average undergraduate tuition (KRW per year), scholarship per student,
international student count, and the freshman competition / fill rates as reference.
The competition rate is NOT used as a difficulty index: it measures application
volume (e.g. SNU 6.5:1 vs. some mid-ranked universities above 20:1), so difficulty
for Korea comes from another indicator (see docs/ARCHITECTURE.md).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "kr_alimi" / "대학주요정보.xlsx"
OUT = ROOT / "data" / "catalogue" / "kr_institutions_alimi.json"


def num(value):
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def main() -> int:
    rows = list(openpyxl.load_workbook(SRC, read_only=True).active.iter_rows(values_only=True))
    header = [str(h).split("\n")[0].strip() for h in rows[0]]
    col = {name: i for i, name in enumerate(header)}
    out = []
    for r in rows[1:]:
        name = str(r[col["학교명"]]).strip()
        quota = num(r[col["입학정원"]])
        if not quota:  # campuses with no intake
            continue
        tuition_thousand = num(r[col["평균 등록금"]])
        out.append({
            "universityName": re.sub(r"\(.*?\)$", "", name).strip(),
            "campusName": name,
            "campusType": r[col["본분교명"]],
            "region": r[col["지역명"]],
            "foundingType": r[col["설립유형"]],
            "admissionQuota": quota,
            "freshmanCompetitionRate": num(r[col["신입생 경쟁률"]]),
            "freshmanFillRate": num(r[col["신입생 충원율"]]),
            "internationalStudents": num(r[col["외국인 학생 수"]]),
            "scholarshipPerStudentKRW": num(r[col["학생 1인당 연간 장학금"]]),
            "undergradTuitionKRW": round(tuition_thousand * 1000) if tuition_thousand else None,
            "dataYear": 2026,
            "source": "대학알리미 대학주요정보 (academyinfo.go.kr)",
            "sourceUrl": "https://www.academyinfo.go.kr/main/main2130/doInit.do",
        })
    OUT.write_text(json.dumps({"source": "https://www.academyinfo.go.kr", "institutions": out}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Saved {len(out)} campuses ({sum(1 for i in out if i['undergradTuitionKRW'])} with tuition) to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
