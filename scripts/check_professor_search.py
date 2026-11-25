"""Live check of "Find professors" on the 5-country department set (F05).

Runs the same pipeline as the result-card button (Gemini web search -> official page check ->
names verified on the page -> OpenAlex) for each department in data/professors/departments.yaml,
and saves what was found. Use it to see how well the button works in each country.

    python scripts/check_professor_search.py                 # all departments
    python scripts/check_professor_search.py --only kr-ajou-computing us-gatech-mechanical

Needs GEMINI_API_KEY (in .env). Output: data/professors/check_<YYYY-MM-DD>.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from admission.faculty import (  # noqa: E402
    candidate_pages, find_professors, gemini_extract_people, gemini_faculty_pages, readable_page_text,
    remember_pages,
)
from admission.openalex import research_for  # noqa: E402
from admission.requirement_finder import _download, _on_domain, fetch_page_text, resolve_url  # noqa: E402

DEPARTMENTS = ROOT / "data" / "professors" / "departments.yaml"
CATALOGUE = ROOT / "data" / "catalogue" / "programs_unified.json"


def programme_for(department: dict, catalogue: list[dict]) -> dict | None:
    """A master's programme of this university whose name matches the department keywords."""
    for level in ("master", "phd"):
        for program in catalogue:
            if (program.get("universityKey") == department["universityKey"] and program["degreeLevel"] == level
                    and any(k.lower() in program["programName"].lower() for k in department["programKeywords"])):
                return {**program, "universityNameEnglish": department["university"]}
    return None


def official_ok(url: str, domains: tuple[str, ...]) -> str | None:
    url = resolve_url(url.rstrip(".,);"))
    if not _on_domain(url, domains, check_alias=True):
        return None
    status, _ = fetch_page_text(url)
    if status != 200:
        print(f"    page check {url} -> HTTP {status}")
    return url if status == 200 else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--only", nargs="*", help="department ids to check")
    args = parser.parse_args(argv)

    from dotenv import load_dotenv
    from google import genai

    load_dotenv(ROOT / ".env")
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY is missing (.env).")
        return 1
    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    from google.genai import types

    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=60_000))
    search_client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=120_000))

    from admission.openalex import _get

    try:
        # a search, not a single-record lookup: searches are what use up the daily budget
        _get("/works", {"search": "NVMeVirt", "per-page": 1, "select": "id"})
        print("OpenAlex: ok" + ("" if os.getenv("OPENALEX_API_KEY") else " (no OPENALEX_API_KEY: small daily limit)"))
    except Exception as error:
        print(f"OpenAlex: NOT AVAILABLE ({type(error).__name__}: {error}). Papers will be empty. "
              "Set OPENALEX_API_KEY in .env (free at openalex.org).")

    departments = yaml.safe_load(DEPARTMENTS.read_text(encoding="utf-8"))["departments"]
    if args.only:
        departments = [d for d in departments if d["id"] in set(args.only)]
    catalogue = json.loads(CATALOGUE.read_text(encoding="utf-8"))["programs"]

    rows = []
    for department in departments:
        program = programme_for(department, catalogue)
        started = time.perf_counter()
        row = {"id": department["id"], "country": department["country"], "university": department["university"],
               "department": department["department"], "programId": program and program["programId"]}
        if not program:
            row.update(status="no_programme")
        else:
            domains = tuple(department["domains"])
            try:
                result = find_professors(
                    program, {"applicantType": program["degreeLevel"]},
                    find_pages=lambda p: candidate_pages(
                        p, lambda q: gemini_faculty_pages(search_client, model, q, domains),
                        on_error=lambda e: print(f"    web search failed: {type(e).__name__}: {str(e)[:80]}"),
                        links_of=lambda url: list(_download(url)[2])),
                    check=lambda url: official_ok(url, domains),
                    fetch=readable_page_text,
                    extract=lambda text, p: gemini_extract_people(client, model, text, p),
                    research=research_for, limit=20,
                )
                remember_pages(program, result["facultyPages"])
                row.update(status="found" if result["found"] else "not_found",
                           facultyPages=result["facultyPages"], tried=result.get("tried", []),
                           professors=result["professors"])
            except Exception as error:  # record and continue with the next department
                row.update(status="error", error=f"{type(error).__name__}: {error}")
        row["seconds"] = round(time.perf_counter() - started, 1)
        professors = row.get("professors") or []
        with_research = sum(1 for p in professors if p.get("recentWorks"))
        print(f"{row['id']:26} {row['status']:12} professors={len(professors):3} "
              f"with_papers={with_research:3} {row['seconds']:6.1f}s")
        if row["status"] == "not_found":
            for attempt in row.get("tried") or [{"url": "-", "result": "web search returned no official page"}]:
                print(f"    tried {attempt['url']}  ->  {attempt['result']}")
        rows.append(row)

    out = ROOT / "data" / "professors" / f"check_{date.today().isoformat()}.json"
    out.write_text(json.dumps({"checkedAt": date.today().isoformat(), "model": model, "departments": rows},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    found = sum(r["status"] == "found" for r in rows)
    print(f"\nFound professors for {found}/{len(rows)} departments. Saved {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
