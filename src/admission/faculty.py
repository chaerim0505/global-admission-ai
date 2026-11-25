"""지도교수 찾기 (SPEC F05, AC8, AC18) — 결과 카드에서 버튼을 누른 과정에 대해 그 자리에서 찾는다.

모든 대학의 교수를 미리 모으지 않는다. 사용자가 고른 과정 하나에 대해서만:
  1. 그 대학 공식 도메인에서 학과 교수진 페이지를 찾는다 (find_pages).
  2. 공식 도메인의 진짜 페이지인지 확인한다 (check: 404 페이지, 사진, 다른 사이트 제외).
  3. 페이지 글에서 이름과 직함을 뽑는다 (extract).
  4. 페이지에 실제로 적힌 이름만 남긴다. 그 페이지 링크가 과정과의 관계 근거다 (AC18).
  5. 연구 정보(연구 분야, 최근 논문)를 붙인다 (research, 선택).
  6. 관심 분야와 겹치는 정도로 순서를 정한다.
학부 과정이나 학부 지원자에게는 교수 후보를 내지 않는다 (AC8).
네트워크·모델 호출은 모두 함수로 주입받아, 테스트는 고정 데이터로 돌린다.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date

PROFESSOR_WORDS = (
    "professor", "lecturer", "reader", "hoogleraar", "hoogleraren", "chair",
    "교수", "부교수", "조교수", "교원",  # 교원: Korean lists headed 전임교원 / 특임교원
)
EXCLUDED_WORDS = (
    "emeritus", "emerita", "retired", "visiting", "adjunct", "honorary", "phd student",
    "doctoral student", "postdoc", "research assistant", "administrator", "secretary",
    "명예", "초빙", "겸임", "객원", "대학원생", "행정",
    "in memoriam", "memoriam", "deceased", "former ",
)
HONORIFICS = r"(?:prof(?:essor)?|dr|mr|mrs|ms|miss|sir|dame|assoc\.?\s*prof|assistant\s+prof)\.?"
DEGREES = r"(?:ph\.?\s*d|d\.?\s*phil|m\.?\s*sc|b\.?\s*sc|m\.?\s*eng|meng|msc|bsc|pe|frs|freng|fieee|ieee fellow)\.?"
NOT_ALLOWED = "Advisor matching is only for master's and PhD programmes."


class AdvisorNotAllowed(ValueError):
    """AC8: advisor matching was requested for an undergraduate programme or applicant."""


def is_professor(title: str | None) -> bool:
    """Teaching and supervising academic staff; not emeritus, visiting, students or admin."""
    text = (title or "").lower()
    if not text or any(word in text for word in EXCLUDED_WORDS):
        return False
    return any(word in text for word in PROFESSOR_WORDS)


def _plain(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"\s+", " ", re.sub(r"[.,'’`\-]", " ", text)).strip()


def name_on_page(name: str, page_text: str) -> bool:
    """Is this person's name actually written on the page (any order, accents ignored)?"""
    name, page = _plain(name), _plain(page_text)
    if not name or not page:
        return False
    if name in page:
        return True
    parts = [p for p in name.split() if len(p) > 1]
    if len(parts) < 2:
        return False
    flipped = " ".join(parts[-1:] + parts[:-1])  # "Smith John" for "John Smith"
    if flipped in page:
        return True
    # "J W Smith" on the page for "Jan Willem Smith" (Dutch and UK pages often use initials)
    surname, given = parts[-1], parts[:-1]
    if len(surname) >= 3:
        initials = r"\s*".join(re.escape(g[0]) for g in given)
        if re.search(rf"(?<![a-z]){initials}\s+(?:[a-z]{{1,3}}\s+)*{re.escape(surname)}(?![a-z])", page):
            return True
    return False


def clean_name(name: str) -> str:
    """Name for display: no titles (Dr., Prof.), degrees (Ph.D.) or notes in brackets."""
    text = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", name or "")
    text = re.sub(r"^\s*(?:(?:prof|dr|ir|ing|drs|mr|em)\.\s*)+", "", text, flags=re.I)  # Dutch "prof.dr.ir."
    text = re.sub(rf"^\s*(?:{HONORIFICS}\s+)+", "", text, flags=re.I)
    text = re.sub(rf"(?:,?\s*{DEGREES})+\s*$", "", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip(" ,;")


def search_name(name: str) -> str:
    """Name to look up in OpenAlex: Latin part of "강태엽 Tae Yeob Kang", "Kim, Dong-Kwon" -> "Dong-Kwon Kim"."""
    text = clean_name(name)
    latin = re.sub(r"[\uac00-\ud7a3]+", " ", text).strip(" ,")
    if latin and latin != text and re.search(r"[A-Za-z]", latin):
        text = latin
    if text.count(",") == 1:
        last, first = (part.strip() for part in text.split(","))
        if first and last:
            text = f"{first} {last}"
    return re.sub(r"\s+", " ", text).strip()


def verify_people(candidates: list[dict], page_text: str) -> list[dict]:
    """Keep professors whose names are on the page; drop invented names, non-professors and repeats."""
    kept, seen = [], set()
    for person in candidates or []:
        if not isinstance(person, dict):
            continue
        raw = str(person.get("name") or "").strip()
        title = str(person.get("title") or "").strip()
        name = clean_name(raw) or raw
        key = _plain(search_name(raw))
        # Dutch pages put the rank in the name ("prof.dr. A. Bozzon") and a research chair as the title
        prof_in_name = bool(re.match(r"\s*prof", raw, flags=re.I)) and not any(w in title.lower() for w in EXCLUDED_WORDS)
        if not name or key in seen or not (is_professor(title) or prof_in_name):
            continue
        if not (name_on_page(raw, page_text) or name_on_page(name, page_text)):
            continue
        seen.add(key)
        record = {"name": name, "title": title}
        # research field and paper titles written next to the name, kept only if really on the page
        field = str(person.get("field") or "").strip()
        if field and _plain(field) in _plain(page_text):
            record["field"] = field
        papers = [str(t).strip() for t in person.get("papers") or [] if str(t).strip()]
        papers = [t for t in papers if len(t) >= 15 and _plain(t)[:60] in _plain(page_text)]
        if papers:
            record["papers"] = papers[:3]
        kept.append(record)
    return kept


GENERIC_WORDS = {
    "system", "systems", "and", "for", "with", "the", "based", "analysis", "application", "applications",
    "advanced", "advancement", "advancements", "method", "methods", "technology", "technologies",
    "technique", "techniques", "research", "engineering", "science", "sciences", "study", "studies",
    "theory", "design", "data", "novel", "using", "from", "their", "this", "that",
}


def _stems(text: str) -> set[str]:
    words = re.findall(r"[a-z]{4,}", (text or "").lower())
    return {w[:-1] if w.endswith("s") and len(w) > 4 else w for w in words if w not in GENERIC_WORDS}


def keep_matching_field(professor: dict, found: dict, shown: int = 3) -> dict | None:
    """Keep only OpenAlex topics and papers that fit the field written on the official page.

    OpenAlex sometimes merges two researchers with the same name into one profile (e.g. a networking
    professor and a chemist). When the page gives the field in English, research that shares no word
    with it is dropped; if nothing fits, nothing is linked.
    """
    stems = _stems(professor.get("field") or "")
    topics = list(found.get("researchTopics") or [])
    works = list(found.get("recentWorks") or [])
    if stems:
        fits = lambda text: any(stem in _plain(text) for stem in stems)
        topics = [t for t in topics if fits(t)]
        works = [w for w in works if fits(f"{w.get('title') or ''} {w.get('abstract') or ''}")]
        if not topics and not works:
            return None
    return {**found, "researchTopics": topics, "recentWorks": works[:shown]}


def _ask_research(research, professor: dict, program: dict):
    """research(name, program) or, if it takes it, research(name, program, person=...)."""
    import inspect

    try:
        takes_person = "person" in inspect.signature(research).parameters
    except (TypeError, ValueError):
        takes_person = False
    name = search_name(professor["name"])
    return research(name, program, person=professor) if takes_person else research(name, program)


def _words(texts) -> set[str]:
    return {w for text in texts for w in re.findall(r"[a-z가-힣]{3,}", str(text or "").lower())}


def interest_score(professor: dict, interests: list[str] | None) -> int:
    """How many interest words appear in the professor's research topics and recent paper titles."""
    if not interests:
        return 0
    research = _words(professor.get("researchTopics") or [])
    research |= _words([professor.get("field")])
    research |= _words(w.get("title") for w in professor.get("recentWorks") or [])
    research |= _words(w.get("abstract") for w in professor.get("recentWorks") or [])
    return len(_words(interests) & research)


def find_professors(program: dict, context: dict | None, *, find_pages, check, fetch, extract,
                    research=None, today: str | None = None, limit: int = 8,
                    enough: int = 5, max_pages: int = 7, research_cap: int = 30) -> dict:
    """Professors for one programme, each tied to the official faculty page that lists them.

    find_pages(program) -> candidate URLs; check(url) -> real official URL or None;
    fetch(url) -> page text; extract(page_text, program) -> [{"name", "title"}];
    research(name, program) -> {"researchTopics": [...], "recentWorks": [...]} or None.
    Stops after the first page that lists at least `enough` professors, so a college-wide
    directory read later cannot add people from other departments.
    """
    from concurrent.futures import ThreadPoolExecutor
    from itertools import islice

    context = context or {}
    if program.get("degreeLevel") == "undergraduate" or context.get("applicantType") == "undergraduate":
        raise AdvisorNotAllowed(NOT_ALLOWED)

    today = today or date.today().isoformat()
    professors: list[dict] = []
    pages: list[str] = []
    tried: list[dict] = []
    seen: set[str] = set()
    # find_pages may be a generator: pages after the first good one (e.g. a slow web search) are never asked for
    for url in islice(iter(find_pages(program) or []), max_pages):
        real = check(url)
        if not real:
            tried.append({"url": url, "result": "not an official page"})
            continue
        if real in pages:
            continue
        text = fetch(real) or ""
        candidates = extract(text, program) or []
        people = verify_people(candidates, text)
        tried.append({"url": real, "result": f"{len(people)} professors confirmed of {len(candidates)} names"
                      if candidates else "no names in the page text (may load with JavaScript)"})
        if not people:
            continue
        pages.append(real)
        for person in people:
            key = _plain(search_name(person["name"]))
            if key in seen:
                continue
            seen.add(key)
            professors.append({
                **person,
                "university": program.get("universityNameEnglish") or program.get("universityName"),
                "country": program.get("country"),
                "programId": program.get("programId"),
                "programRelationSource": real,
                "verificationStatus": "official_faculty_page",
                "checkedAt": today,
                "researchTopics": [],
                "recentWorks": [],
            })
        if len(people) >= enough:
            break

    if research and professors:
        professors.sort(key=lambda p: _plain(p["name"]))  # the same order they are shown in when no interests
        batch = professors[:research_cap]
        with ThreadPoolExecutor(max_workers=4) as pool:  # OpenAlex allows a few requests at a time
            found_all = list(pool.map(lambda p: _ask_research(research, p, program), batch))
        for record, found in zip(batch, found_all):
            found = keep_matching_field(record, found) if found else None
            if found:
                record["researchTopics"] = list(found.get("researchTopics") or [])
                record["recentWorks"] = list(found.get("recentWorks") or [])
                record["researchSource"] = found.get("source")

    interests = context.get("interests") or []
    professors.sort(key=lambda p: (-interest_score(p, interests), _plain(p["name"])))
    return {
        "professors": professors[:limit],
        "facultyPages": pages,
        "tried": tried,
        "found": bool(professors),
    }


# ---------------------------------------------------------------------------
# Remembered faculty pages
# ---------------------------------------------------------------------------

PAGES_FILE = __import__("pathlib").Path(__file__).resolve().parents[2] / "data" / "professors" / "faculty_pages.json"


def page_keys(program: dict) -> list[str]:
    university = program.get("universityKey") or program.get("universityName") or ""
    return [f"{university}|{field}" for field in program.get("engineeringFields") or []]


def known_pages(program: dict, path=None) -> list[str]:
    """Official faculty pages found before for this university and field (checked again before use)."""
    import json

    path = path or PAGES_FILE
    try:
        pages = json.loads(path.read_text(encoding="utf-8")).get("pages") or {}
    except (OSError, ValueError):
        return []
    found = [url for key in page_keys(program) for url in pages.get(key) or []]
    return list(dict.fromkeys(found))


def remember_pages(program: dict, urls: list[str], path=None) -> None:
    """Keep pages that worked, so the next search for this department skips the web search."""
    import json

    path = path or PAGES_FILE
    if not urls or not page_keys(program):
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {"pages": {}}
    pages = data.setdefault("pages", {})
    for key in page_keys(program):
        pages[key] = list(dict.fromkeys(urls + (pages.get(key) or [])))[:3]
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:  # read-only deployment: just skip
        pass


FACULTY_LINK_WORDS = ("faculty", "professor", "people", "staff", "member", "교수", "구성원", "교원")


def faculty_links(url: str, links: list[str], limit: int = 3) -> list[str]:
    """Links on a department page that look like its faculty list (same site only)."""
    from urllib.parse import urlparse

    host = (urlparse(url).hostname or "").removeprefix("www.")
    found = []
    for link in links:
        target = (urlparse(link).hostname or "").removeprefix("www.")
        if target.endswith(host) and any(w in link.lower() for w in FACULTY_LINK_WORDS) and link != url:
            found.append(link)
    return list(dict.fromkeys(found))[:limit]


def candidate_pages(program: dict, web_search, on_error=None, links_of=None):
    """Remembered pages first (and faculty links found on them); the web search runs only if
    none of them gave professors.

    links_of(url) -> links on that page, used when a remembered page is a department home page.
    A failed web search (e.g. time-out) ends the list instead of the whole search, so the
    result still says which pages were tried.
    """
    for url in known_pages(program):
        yield url
        if links_of:
            try:
                yield from faculty_links(url, links_of(url))
            except Exception:
                pass
    try:
        found = list(web_search(program))
    except Exception as error:
        if on_error:
            on_error(error)
        return
    yield from found


# ---------------------------------------------------------------------------
# Live helpers (Gemini, web, OpenAlex). Not used by the tests.
# ---------------------------------------------------------------------------

def _generate(client, model: str, contents: str, low_thinking: bool = True, **config):
    """Gemini call with one retry after a time-out, as in AI exploration; low thinking when asked."""
    from google.genai import types

    from admission.ai_exploration import ATTEMPTS, THINKING_LEVEL, ExplorationTimeout, _is_timeout

    plain = types.GenerateContentConfig(temperature=0, **config)
    settings = plain
    if low_thinking and THINKING_LEVEL:
        try:
            settings = types.GenerateContentConfig(
                temperature=0, thinking_config=types.ThinkingConfig(thinking_level=THINKING_LEVEL), **config)
        except Exception:
            settings = plain
    for attempt in range(1, ATTEMPTS + 1):
        try:
            return client.models.generate_content(model=model, contents=contents, config=settings)
        except Exception as error:
            text = str(error)
            if settings is not plain and ("400" in text or "INVALID_ARGUMENT" in text):
                settings = plain
                if attempt < ATTEMPTS:
                    continue
            if not _is_timeout(error):
                raise
            if attempt == ATTEMPTS:
                raise ExplorationTimeout(text) from error
    raise ExplorationTimeout("no answer")


# Korean department names that usually run each field's graduate programmes. Our catalogue often has
# an English programme name ("Computer Engineering") while the department site is in Korean.
KO_DEPARTMENTS = {
    "computing": "소프트웨어학과, 컴퓨터공학과, 정보컴퓨터공학과, 인공지능학과",
    "electrical_electronic": "전자공학과, 전기공학과, 전자전기공학부",
    "mechanical": "기계공학과",
    "civil_environmental": "건설시스템공학과, 토목공학과, 환경공학과",
    "chemical_materials": "화학공학과, 신소재공학과",
    "industrial_systems": "산업공학과",
    "aerospace": "항공우주공학과",
    "biomedical": "의공학과, 바이오메디컬공학과",
}


def local_search_hint(program: dict) -> str:
    """Extra search words in the local language, e.g. "아주대학교 소프트웨어학과 교수진" for a Korean programme."""
    if program.get("country") != "KR":
        return ""
    university = program.get("universityName") or ""
    names = [KO_DEPARTMENTS[f] for f in program.get("engineeringFields") or [] if f in KO_DEPARTMENTS]
    korean_programme = program.get("programName") if re.search(r"[\uac00-\ud7a3]", program.get("programName") or "") else ""
    departments = ", ".join(x for x in [korean_programme, *names] if x)
    return (f"\nThe department website is likely in Korean. Search in Korean too, for example "
            f'"{university} {departments.split(", ")[0] if departments else ""} 교수진" or "교수소개". '
            f"The department may be one of: {departments}. Department sites are often on a subdomain "
            f"of the university domain (e.g. <department>.{program.get('officialDomain') or 'university.ac.kr'}).")


def gemini_faculty_pages(client, model: str, program: dict, domains: tuple[str, ...]) -> list[str]:
    """Ask Gemini (Google Search) for the official faculty directory page of this programme's department."""
    from google.genai import types

    from admission.requirement_finder import grounding_urls, parse_object

    university = program.get("universityNameEnglish") or program.get("universityName")
    prompt = f"""Find the official page that lists the academic staff (professors) of the department
that runs this programme. Use only the university's official website ({", ".join(domains)}).

University: {university} ({program.get("universityName")})
Programme: {program.get("programName")} ({program.get("degreeLevel")})
{local_search_hint(program)}

Prefer a page whose HTML itself lists the names (a staff list or the university research portal's
list of people in this department, e.g. a Pure / research-portal "persons" page on the same domain).
Avoid college-wide directories that mix several departments.

Reply with ONLY JSON: {{"pages": ["https://...", ...]}} with up to 3 official faculty or people
directory pages, best first. Do not invent URLs."""
    # Finding the right page needs normal reasoning; with low thinking the model guessed URLs.
    response = _generate(client, model, prompt, low_thinking=False,
                         tools=[types.Tool(google_search=types.GoogleSearch())])
    data = parse_object(response.text or "") or {}
    written = [str(u) for u in data.get("pages") or [] if str(u).startswith("https://")]
    searched = grounding_urls(response)
    # Pages the search actually returned and the model also named come first, then other search
    # results, then URLs the model only wrote (those can be guesses and often 404).
    both = [u for u in written if u in searched]
    return list(dict.fromkeys(both + searched + written))[:5]


def gemini_extract_people(client, model: str, page_text: str, program: dict) -> list[dict]:
    """Ask Gemini to copy names and job titles from the page text (no search, no guessing)."""
    import json

    prompt = f"""Below is the text of an official university web page. List the people on it who are
academic staff of the department, with their job title exactly as written on the page.
If the page lists people under a heading such as "Professors", "Full professors" or "교수진"
and gives no title next to each name, use that heading as their title.
Copy each name exactly as written, including initials and titles (e.g. "prof.dr.ir. J.W. Smith").
Do not expand initials. Do not add anyone who is not in the text.
If the page writes a research field (e.g. "전공", "Research interests") next to a person, copy it
exactly as "field". If it lists paper titles next to a person, copy up to 3 of them exactly as "papers".
Leave them out when the page does not write them.

Reply with ONLY a JSON array: [{{"name": "...", "title": "...", "field": "...", "papers": ["..."]}}]

Page text:
{page_text[:30000]}"""
    response = _generate(client, model, prompt, response_mime_type="application/json")
    try:
        data = json.loads(response.text or "[]")
    except ValueError:
        return []
    return data if isinstance(data, list) else []


def readable_page_text(url: str) -> str:
    """Page text with its original letter case (names), scripts and tags removed."""
    import html

    import requests

    try:
        response = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0 (admission-ai faculty check)"})
    except Exception:  # a slow or refused page counts as a page without names
        return ""
    raw = response.text
    raw = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"<br\s*/?>|</(p|div|li|tr|h\d)>", "\n", raw, flags=re.I)
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", text)).strip()
