"""Collect researcher and publication data from OpenAlex for professor matching (F05).

Run from the repo root on a machine with internet access:

    python scripts/collect_researchers_openalex.py
    python scripts/collect_researchers_openalex.py --universities "Ajou University" --per-field 10

Standard library only. Optional environment variables:
    OPENALEX_API_KEY  free key from openalex.org (raises the daily budget)
    OPENALEX_MAILTO   contact email sent with requests

Output: data/professors/researchers_openalex.json and data/professors/institutions_openalex.json.

OpenAlex lists everyone who publishes with an affiliation, not only professors.
Every record is saved as role "unverified_researcher" and verificationStatus
"needs_review" until a team member confirms the person on the official
faculty page.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Callable

BASE = "https://api.openalex.org"
ROOT = Path(__file__).resolve().parents[1]
PROGRAMS = ROOT / "data" / "programs_integrated.json"
OUT_DIR = ROOT / "data" / "professors"

# Our engineering fields -> OpenAlex topic hierarchy names (field or subfield).
FIELD_MAP: dict[str, dict[str, set[str]]] = {
    "computing": {"field": {"Computer Science"}, "subfield": set()},
    "electrical_electronic": {"field": set(), "subfield": {"Electrical and Electronic Engineering"}},
    "mechanical": {"field": set(), "subfield": {"Mechanical Engineering"}},
    "chemical_materials": {"field": {"Chemical Engineering", "Materials Science"}, "subfield": set()},
}

AUTHOR_SELECT = "id,display_name,orcid,works_count,cited_by_count,summary_stats,last_known_institutions,topics"
WORK_SELECT = "id,title,publication_year,doi,authorships,primary_topic"

Fetch = Callable[[str, dict], dict]


def http_fetch(path: str, params: dict) -> dict:
    params = dict(params)
    if os.getenv("OPENALEX_API_KEY"):
        params["api_key"] = os.environ["OPENALEX_API_KEY"]
    if os.getenv("OPENALEX_MAILTO"):
        params["mailto"] = os.environ["OPENALEX_MAILTO"]
    url = f"{BASE}{path}?{urllib.parse.urlencode(params, safe=':|,')}"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                time.sleep(0.15)
                return json.load(response)
        except Exception as error:  # network, 429, 5xx
            if attempt == 3:
                raise RuntimeError(f"OpenAlex request failed: {url}\n{error}") from error
            time.sleep(2 * (attempt + 1))
    return {}


def short_id(openalex_id: str) -> str:
    return openalex_id.rsplit("/", 1)[-1]


def load_universities(path: Path = PROGRAMS) -> list[tuple[str, str]]:
    programs = json.loads(path.read_text(encoding="utf-8"))
    return sorted({(p["universityName"], p["country"]) for p in programs})


def resolve_institution(fetch: Fetch, name: str, country: str) -> dict | None:
    data = fetch("/institutions", {
        "search": name,
        "filter": f"country_code:{country}",
        "per-page": 3,
        "select": "id,display_name,country_code,ror",
    })
    results = data.get("results") or []
    return results[0] if results else None


def classify_author(author: dict) -> str | None:
    """Pick our engineering field from the author's top OpenAlex topics."""
    scores: Counter = Counter()
    total = 0
    for topic in (author.get("topics") or [])[:5]:
        count = topic.get("count") or 1
        total += count
        field = (topic.get("field") or {}).get("display_name")
        subfield = (topic.get("subfield") or {}).get("display_name")
        for ours, names in FIELD_MAP.items():
            if field in names["field"] or subfield in names["subfield"]:
                scores[ours] += count
    if not scores or total == 0:
        return None
    best, score = scores.most_common(1)[0]
    return best if score / total >= 0.3 else None


def is_current_member(author: dict, institution_id: str) -> bool:
    return any(i.get("id") == institution_id for i in author.get("last_known_institutions") or [])


def top_authors(fetch: Fetch, institution_id: str, pages: int) -> list[dict]:
    authors: list[dict] = []
    for page in range(1, pages + 1):
        data = fetch("/authors", {
            "filter": f"last_known_institutions.id:{short_id(institution_id)}",
            "sort": "works_count:desc",
            "per-page": 100,
            "page": page,
            "select": AUTHOR_SELECT,
        })
        results = data.get("results") or []
        authors.extend(results)
        if len(results) < 100:
            break
    return authors


def recent_works(fetch: Fetch, author_ids: list[str], since: str, per_author: int) -> dict[str, list[dict]]:
    works: dict[str, list[dict]] = {a: [] for a in author_ids}
    for start in range(0, len(author_ids), 25):
        chunk = author_ids[start:start + 25]
        data = fetch("/works", {
            "filter": f"authorships.author.id:{'|'.join(short_id(a) for a in chunk)},from_publication_date:{since}",
            "sort": "publication_date:desc",
            "per-page": 100,
            "select": WORK_SELECT,
        })
        for work in data.get("results") or []:
            for authorship in work.get("authorships") or []:
                aid = (authorship.get("author") or {}).get("id")
                if aid in works and len(works[aid]) < per_author:
                    works[aid].append({
                        "title": work.get("title"),
                        "year": work.get("publication_year"),
                        "doi": work.get("doi"),
                        "openalexUrl": work.get("id"),
                        "topic": (work.get("primary_topic") or {}).get("display_name"),
                    })
    return works


def build_record(author: dict, university: str, country: str, institution: dict, field: str,
                 works: list[dict], today: str) -> dict:
    return {
        "researcherId": short_id(author["id"]),
        "name": author.get("display_name"),
        "orcid": author.get("orcid"),
        "university": university,
        "country": country,
        "institutionId": short_id(institution["id"]),
        "engineeringField": field,
        "researchTopics": [t.get("display_name") for t in (author.get("topics") or [])[:5]],
        "worksCount": author.get("works_count"),
        "citedByCount": author.get("cited_by_count"),
        "hIndex": (author.get("summary_stats") or {}).get("h_index"),
        "recentWorks": works,
        "sourceUrl": author["id"],
        "source": "OpenAlex",
        "checkedAt": today,
        "role": "unverified_researcher",
        "facultyPageUrl": None,
        "verificationStatus": "needs_review",
    }


def collect(fetch: Fetch, universities: list[tuple[str, str]], per_field: int, pages: int,
            since: str, works_per_author: int, today: str, log=print) -> tuple[list[dict], list[dict]]:
    institutions: list[dict] = []
    records: list[dict] = []
    for name, country in universities:
        institution = resolve_institution(fetch, name, country)
        institutions.append({
            "university": name,
            "country": country,
            "openalexId": institution and short_id(institution["id"]),
            "openalexName": institution and institution.get("display_name"),
            "ror": institution and institution.get("ror"),
            "needsReview": institution is None or institution.get("display_name", "").lower() != name.lower(),
        })
        if institution is None:
            log(f"[skip] {name} ({country}): institution not found")
            continue
        chosen: dict[str, list[dict]] = {f: [] for f in FIELD_MAP}
        for author in top_authors(fetch, institution["id"], pages):
            if not is_current_member(author, institution["id"]):
                continue
            field = classify_author(author)
            if field and len(chosen[field]) < per_field:
                chosen[field].append(author)
        picked = [(f, a) for f, authors in chosen.items() for a in authors]
        works = recent_works(fetch, [a["id"] for _, a in picked], since, works_per_author)
        for field, author in picked:
            records.append(build_record(author, name, country, institution, field, works[author["id"]], today))
        log(f"[ok] {name}: " + ", ".join(f"{f}={len(a)}" for f, a in chosen.items()))
    return institutions, records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--universities", nargs="*", help="Limit to these university names")
    parser.add_argument("--per-field", type=int, default=10, help="Researchers per university and field")
    parser.add_argument("--pages", type=int, default=3, help="Author pages (100 each) to scan per university")
    parser.add_argument("--since", default="2022-01-01", help="Recent works from this date")
    parser.add_argument("--works-per-author", type=int, default=5)
    args = parser.parse_args(argv)

    universities = load_universities()
    if args.universities:
        wanted = {u.lower() for u in args.universities}
        universities = [u for u in universities if u[0].lower() in wanted]
    today = date.today().isoformat()
    institutions, records = collect(http_fetch, universities, args.per_field, args.pages,
                                    args.since, args.works_per_author, today)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "institutions_openalex.json").write_text(
        json.dumps(institutions, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / "researchers_openalex.json").write_text(json.dumps({
        "checkedAt": today,
        "source": "OpenAlex (https://openalex.org), CC0",
        "note": "Researchers affiliated with each university, not confirmed professors. Confirm on the official faculty page before use.",
        "researchers": records,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(records)} researchers from {len(institutions)} universities to {OUT_DIR}")
    review = [i["university"] for i in institutions if i["needsReview"]]
    if review:
        print("Check institution match for:", ", ".join(review))
    return 0


if __name__ == "__main__":
    sys.exit(main())
