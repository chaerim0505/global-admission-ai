"""OpenAlex 연구 정보 (F05) — 공식 교수진 페이지에서 확인한 교수에게 연구 분야와 최근 논문을 붙인다.

OpenAlex(https://openalex.org, CC0)는 누가 교수인지, 어느 학과인지는 알려 주지 않는다.
그래서 교수 여부와 과정 관계는 공식 페이지로 정하고(faculty.py), 여기서는 같은 대학 소속인
같은 이름의 연구자를 찾아 연구 정보만 가져온다. 소속 대학이 다르면 연결하지 않는다.

한국어 페이지처럼 이름이 한글로만 적혀 있으면 이름 검색은 쓰지 않는다 (같은 대학에 동명이인이 있다).
대신 공식 페이지에 그 교수 이름 옆에 적힌 논문 제목으로 OpenAlex 논문을 찾고, 그 논문의 저자 중
한글 이름과 로마자 표기가 맞고(성 + 이름 첫 글자) 같은 대학 소속 이력이 있는 한 사람만 연결한다.
후보가 둘 이상이면 연결하지 않는다.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from functools import lru_cache

BASE = "https://api.openalex.org"


class BudgetExhausted(RuntimeError):
    """OpenAlex daily budget for this API key is used up (resets at midnight UTC)."""


_BUDGET_OUT = {"until": 0.0}


def _get(path: str, params: dict) -> dict:
    # once the daily budget is used up, every request fails: stop asking instead of retrying for minutes
    if time.time() < _BUDGET_OUT["until"]:
        raise BudgetExhausted("OpenAlex daily budget used up")
    params = dict(params)
    if os.getenv("OPENALEX_API_KEY"):
        params["api_key"] = os.environ["OPENALEX_API_KEY"]
    if os.getenv("OPENALEX_MAILTO"):
        params["mailto"] = os.environ["OPENALEX_MAILTO"]
    url = f"{BASE}{path}?{urllib.parse.urlencode(params, safe=':|,')}"
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=20) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code == 429:
                try:
                    body = json.loads(error.read() or b"{}")
                except ValueError:
                    body = {}
                if body.get("reason") == "daily_budget":
                    _BUDGET_OUT["until"] = time.time() + min(float(body.get("retryAfter") or 3600), 86400)
                    raise BudgetExhausted(body.get("message") or "OpenAlex daily budget used up") from error
            # 429 = too many requests at once; wait and try again instead of giving up
            if error.code not in (429, 500, 502, 503, 504) or attempt == 4:
                raise
        except urllib.error.URLError:
            if attempt == 4:
                raise
        time.sleep(0.5 * 2 ** attempt)
    return {}


def abstract_text(inverted_index: dict | None, limit: int = 600) -> str | None:
    """OpenAlex stores abstracts as {word: [positions]}; rebuild the text."""
    if not inverted_index:
        return None
    words = sorted((pos, word) for word, positions in inverted_index.items() for pos in positions)
    text = " ".join(word for _, word in words)
    return text[:limit] + ("…" if len(text) > limit else "")


def short_id(openalex_id: str) -> str:
    return str(openalex_id).rsplit("/", 1)[-1]


_INSTITUTIONS: dict[tuple, str] = {}


def institution_id(university_key: str | None, name: str, country: str | None) -> str | None:
    """OpenAlex institution id, from the ROR id when we have it, otherwise by name and country.

    Only found ids are remembered: a failed lookup (e.g. rate limit) is tried again next time.
    """
    key = (university_key, name, country)
    if key not in _INSTITUTIONS:
        found = _institution_lookup(university_key, name, country)
        if not found:
            return None
        _INSTITUTIONS[key] = found
    return _INSTITUTIONS[key]


def _institution_lookup(university_key: str | None, name: str, country: str | None) -> str | None:
    try:
        if university_key and "ror.org/" in university_key:
            data = _get(f"/institutions/ror:{university_key.rsplit('/', 1)[-1]}", {"select": "id"})
            return short_id(data["id"]) if data.get("id") else None
        params = {"search": name, "per-page": 1, "select": "id"}
        if country:
            params["filter"] = f"country_code:{country}"
        results = _get("/institutions", params).get("results") or []
        return short_id(results[0]["id"]) if results else None
    except Exception:
        return None


def pick_author(results: list[dict], name: str, institution: str) -> dict | None:
    """Same name and an affiliation with the same institution; otherwise no match."""
    from admission.faculty import name_on_page

    for author in results or []:
        names = [author.get("display_name") or ""] + list(author.get("display_name_alternatives") or [])
        if not any(name_on_page(name, n) or name_on_page(n, name) for n in names if n):
            continue
        affiliations = {short_id((a.get("institution") or {}).get("id", "")) for a in author.get("affiliations") or []}
        affiliations |= {short_id(i.get("id", "")) for i in author.get("last_known_institutions") or []}
        if institution in affiliations:
            return author
    return None


# ---------------------------------------------------------------------------
# Korean names written only in Hangul
# ---------------------------------------------------------------------------

HANGUL = re.compile(r"^[\uac00-\ud7a3]{2,5}$")
# Common ways each surname is written in English-language papers
SURNAMES = {
    "김": "kim gim", "이": "lee yi rhee rhie li i", "박": "park pak bak", "최": "choi choe",
    "정": "jung jeong chung joung jeung", "강": "kang gang", "조": "cho jo joe", "윤": "yoon yun",
    "장": "jang chang", "임": "lim im yim", "한": "han", "오": "oh o", "서": "seo suh", "신": "shin sin",
    "권": "kwon gwon", "황": "hwang", "안": "ahn an", "송": "song", "전": "jeon jun chun", "홍": "hong",
    "유": "yoo yu you", "고": "ko go koh", "문": "moon mun", "양": "yang", "손": "son sohn",
    "배": "bae pae", "백": "baek paik baik back", "허": "heo huh hur", "남": "nam", "심": "shim sim",
    "노": "noh roh no ro", "하": "ha", "곽": "kwak gwak", "성": "sung seong", "차": "cha",
    "주": "joo ju chu", "우": "woo u", "구": "koo ku gu", "민": "min", "류": "ryu yoo yu lyu rhyu ryoo",
    "나": "na ra", "진": "jin chin", "지": "ji chi", "엄": "eom um", "채": "chae", "원": "won",
    "천": "cheon chun", "방": "bang", "공": "kong gong", "현": "hyun hyeon", "변": "byun byeon pyun",
    "염": "yeom yum", "여": "yeo yuh", "추": "chu choo", "도": "do doh", "소": "so", "석": "seok suk",
    "선": "sun seon", "설": "seol sul", "마": "ma", "길": "gil kil", "연": "yeon yun", "위": "wi wee",
    "표": "pyo", "명": "myung myeong", "기": "ki gi", "반": "ban", "왕": "wang", "금": "keum geum",
    "옥": "ok", "육": "yuk", "인": "in", "맹": "maeng", "제": "je", "모": "mo", "탁": "tak",
    "국": "kook guk", "은": "eun", "편": "pyeon pyun", "용": "yong", "예": "ye", "경": "kyung gyeong",
    "봉": "bong", "부": "boo bu", "황보": "hwangbo", "남궁": "namgung namkung", "제갈": "jegal",
    "선우": "sunwoo seonwoo", "독고": "dokgo",
}
# First letter a romanised given name can start with, by the first consonant of its first syllable
INITIALS = ["gk", "gk", "n", "dt", "dt", "rlny", "m", "bp", "bp", "s", "s", "aeiouwy",
            "jc", "jc", "c", "k", "t", "p", "h"]


def is_hangul_name(name: str) -> bool:
    return bool(HANGUL.match((name or "").replace(" ", "")))


def romanization_fits(korean: str, latin: str) -> bool:
    """Could "Sanghoon Kim" / "Kim, Sang-Hoon" / "S. Kim" be written for 김상훈? (surname + first initial)"""
    from admission.faculty import _plain

    korean = (korean or "").replace(" ", "")
    tokens = _plain(latin).split()
    if not is_hangul_name(korean) or len(tokens) < 2:
        return False
    for size in (2, 1):
        surname, given = korean[:size], korean[size:]
        if surname not in SURNAMES or not given:
            continue
        options = SURNAMES[surname].split()
        initial = INITIALS[(ord(given[0]) - 0xAC00) // 588]
        for i, token in enumerate(tokens):
            if token in options:
                rest = tokens[:i] + tokens[i + 1:]
                if rest and rest[0][0] in initial:
                    return True
    return False


def _same_title(a: str, b: str) -> bool:
    from admission.faculty import _plain

    a, b = _plain(a)[:80], _plain(b)[:80]
    return bool(a) and len(a) >= 15 and (a == b or a.startswith(b) or b.startswith(a))


def paper_title(listed: str) -> str:
    """Title only, from a page line like "NVMeVirt: A Versatile ... Device, USENIX FAST, 2023"."""
    text = re.sub(r"\(\s*(?:19|20)\d{2}[^)]*\)\s*$", "", (listed or "").strip())
    for mark in (", ", ". ", " (", " - "):
        cut = text.find(mark, 20)
        if cut > 0:
            text = text[:cut]
    return text.strip(" .,")


def author_from_papers(korean: str, papers: list[str], institution: str) -> dict | None:
    """The one author who wrote papers listed next to this professor on the official page."""
    votes: dict[str, int] = {}
    for listed in list(papers or [])[:3]:
        title = paper_title(listed)
        query = " ".join(re.sub(r"[^\w\s-]", " ", title).split()[:15])
        if len(query) < 15:
            continue
        try:
            works = _get("/works", {"search": query, "per-page": 5, "select": "id,title,authorships"}).get("results") or []
        except Exception:  # one paper that cannot be searched should not stop the others
            continue
        for work in works:
            if not _same_title(work.get("title") or "", title):
                continue
            for authorship in work.get("authorships") or []:
                author = authorship.get("author") or {}
                if author.get("id") and romanization_fits(korean, author.get("display_name") or ""):
                    votes[author["id"]] = votes.get(author["id"], 0) + 1
            break
    # the author must also have been at this university
    confirmed = []
    for author_id, count in votes.items():
        try:
            author = _get(f"/authors/{short_id(author_id)}",
                          {"select": "id,display_name,affiliations,last_known_institutions,topics"})
        except Exception:
            continue
        affiliations = {short_id((a.get("institution") or {}).get("id", "")) for a in author.get("affiliations") or []}
        affiliations |= {short_id(i.get("id", "")) for i in author.get("last_known_institutions") or []}
        if institution in affiliations:
            confirmed.append((count, author))
    if not confirmed:
        return None
    confirmed.sort(key=lambda pair: -pair[0])
    if len(confirmed) > 1 and confirmed[0][0] == confirmed[1][0]:
        return None  # two people could be this professor: link nobody
    return confirmed[0][1]


def _works_for(author: dict, since: str, per_author: int) -> tuple:
    works = _get("/works", {
        "filter": f"authorships.author.id:{short_id(author['id'])},from_publication_date:{since}",
        "sort": "publication_date:desc", "per-page": per_author,
        "select": "id,title,publication_year,doi,abstract_inverted_index",
    }).get("results") or []
    return (
        author["id"],
        tuple(t.get("display_name") for t in (author.get("topics") or [])[:5]),
        tuple((w.get("title"), w.get("publication_year"), w.get("doi") or w.get("id"),
               abstract_text(w.get("abstract_inverted_index"))) for w in works),
    )


@lru_cache(maxsize=1024)
def _research_by_papers(korean: str, papers: tuple, institution: str, since: str, per_author: int) -> tuple:
    author = author_from_papers(korean, list(papers), institution)
    return _works_for(author, since, per_author) if author else ()


@lru_cache(maxsize=1024)
def _research(name: str, institution: str, since: str, per_author: int) -> tuple:
    data = _get("/authors", {
        "search": name, "per-page": 10,
        "select": "id,display_name,display_name_alternatives,affiliations,last_known_institutions,topics",
    })
    author = pick_author(data.get("results") or [], name, institution)
    if not author:
        return ()
    return _works_for(author, since, per_author)


def research_for(name: str, program: dict, since: str = "2021-01-01", per_author: int = 8,
                 person: dict | None = None) -> dict | None:
    """Research topics and recent papers for a professor confirmed on the official page, or None.

    person: the professor as read from the page ({"name", "papers"}). A Hangul-only name is
    linked only through the papers written next to it on the page, never by name search.
    """
    institution = institution_id(program.get("universityKey"),
                                 program.get("universityNameEnglish") or program.get("universityName") or "",
                                 program.get("country"))
    if not institution:
        return None
    person = person or {}
    korean = (person.get("name") or name or "").replace(" ", "")
    papers = tuple(str(p) for p in person.get("papers") or [] if p)
    try:
        if is_hangul_name(korean):
            found = _research_by_papers(korean, papers, institution, since, per_author) if papers else ()
        else:
            found = _research(name, institution, since, per_author)
    except Exception:
        return None
    if not found:
        return None
    author_id, topics, works = found
    return {
        "source": author_id,
        "researchTopics": list(topics),
        "recentWorks": [{"title": t, "year": y, "url": u, "abstract": a} for t, y, u, a in works],
    }
