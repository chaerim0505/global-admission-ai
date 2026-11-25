"""지도교수 찾기 골든 테스트 — SPEC.md F05, AC8, AC18.

케이스는 tests/harness/advisor_cases.yaml 에서 읽는다. 웹 검색·페이지·모델·OpenAlex 응답은
케이스 데이터로 고정하고, 실제 find_professors 의 규칙(학부 거절, 페이지 확인, 이름 검증,
직함 필터, 관심 분야 순서)을 검사한다.
"""

from pathlib import Path

import pytest
import yaml

from admission.faculty import AdvisorNotAllowed, find_professors

CASES = yaml.safe_load(
    (Path(__file__).resolve().parent / "harness" / "advisor_cases.yaml").read_text(encoding="utf-8")
)["cases"]
KNOWN_EXPECTED_KEYS = {"refused", "professors", "absent", "found", "relation", "no_papers", "has_papers"}


def test_case_file_is_valid():
    ids = [case["id"] for case in CASES]
    assert len(ids) == len(set(ids))
    for case in CASES:
        assert {"id", "ac", "category", "program", "context", "pages", "expected"} <= set(case)
        assert case["category"] in {"normal", "boundary", "forbidden"}
        # a misspelled key would otherwise pass without being checked
        assert not set(case["expected"]) - KNOWN_EXPECTED_KEYS


def _run(case):
    pages = {page["url"]: page for page in case["pages"]}
    research = case.get("research") or {}
    return find_professors(
        case["program"], case["context"],
        find_pages=lambda program: list(pages),
        check=lambda url: url if pages[url]["official"] else None,
        fetch=lambda url: pages[url]["text"],
        extract=lambda text, program: next(p["people"] for p in pages.values() if p["text"] == text),
        research=lambda name, program: research.get(name),
        today="2026-11-25",
    )


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_advisor_case(case):
    expected = case["expected"]
    if expected.get("refused"):
        with pytest.raises(AdvisorNotAllowed):
            _run(case)
        return

    result = _run(case)
    names = [p["name"] for p in result["professors"]]

    if "professors" in expected:
        assert names == expected["professors"]
    for name in expected.get("absent", []):
        assert name not in names
    if "found" in expected:
        assert result["found"] is expected["found"]
    if "relation" in expected:
        assert all(p["programRelationSource"] == expected["relation"] for p in result["professors"])
    for name in expected.get("has_papers", []):
        assert next(p for p in result["professors"] if p["name"] == name)["recentWorks"]
    for name in expected.get("no_papers", []):
        assert next(p for p in result["professors"] if p["name"] == name)["recentWorks"] == []

    # AC18 for every case: each professor is tied to an official page that was checked, for this programme.
    for professor in result["professors"]:
        assert professor["programRelationSource"] in result["facultyPages"]
        assert professor["programId"] == case["program"]["programId"]
        assert professor["verificationStatus"] == "official_faculty_page"


def test_web_search_is_skipped_when_a_remembered_page_works(tmp_path):
    """A remembered official page that lists enough professors means no slow web search."""
    from admission.faculty import candidate_pages, known_pages, remember_pages

    store = tmp_path / "faculty_pages.json"
    program = {"programId": "p1", "degreeLevel": "master", "universityKey": "U1",
               "engineeringFields": ["computing"], "universityName": "Test University"}
    remember_pages(program, ["https://www.test.edu/cs/faculty"], path=store)
    assert known_pages(program, path=store) == ["https://www.test.edu/cs/faculty"]

    text = "Ann Ash Professor. Ben Birch Professor. Cy Cedar Professor. Di Dogwood Professor. Ed Elm Professor."
    people = [{"name": n, "title": "Professor"} for n in ["Ann Ash", "Ben Birch", "Cy Cedar", "Di Dogwood", "Ed Elm"]]

    def web_search(_):
        raise AssertionError("web search should not run")

    def pages(p):
        yield from known_pages(p, path=store)
        yield from web_search(p)

    result = find_professors(program, {"applicantType": "master"}, find_pages=pages,
                             check=lambda url: url, fetch=lambda url: text,
                             extract=lambda t, p: people, today="2026-11-25")
    assert len(result["professors"]) == 5
    assert result["facultyPages"] == ["https://www.test.edu/cs/faculty"]
    assert candidate_pages  # exported for the app


def test_faculty_links_on_a_department_home_page_are_followed():
    """A remembered department home page leads to its faculty list on the same site only."""
    from admission.faculty import faculty_links

    links = ["https://software.ajou.ac.kr/software/intro/professor.do", "https://www.ajou.ac.kr/kr/index.do",
             "https://software.ajou.ac.kr/software/board/notice.do", "https://ratemyprof.example/ajou/faculty"]
    assert faculty_links("https://software.ajou.ac.kr/", links) == [
        "https://software.ajou.ac.kr/software/intro/professor.do"]


def test_korean_page_keeps_field_and_papers_written_next_to_the_name():
    """전임교원 lists: title from the heading, 전공 and paper titles kept only if they are on the page."""
    from admission.faculty import verify_people

    text = ("교수진 강경란 korykang@ajou.ac.kr 전공 Internet Multicast, Embedded Network Software "
            "A Scalable Joint Routing and Scheduling Scheme for Large-scale Wireless Sensor Networks (2013)")
    people = verify_people([{"name": "강경란", "title": "전임교원",
                             "field": "Internet Multicast, Embedded Network Software",
                             "papers": ["A Scalable Joint Routing and Scheduling Scheme for Large-scale Wireless Sensor Networks",
                                        "An Invented Paper Title That Is Not On The Page"]},
                            {"name": "홍길동", "title": "전임교원"}], text)
    assert people == [{"name": "강경란", "title": "전임교원",
                       "field": "Internet Multicast, Embedded Network Software",
                       "papers": ["A Scalable Joint Routing and Scheduling Scheme for Large-scale Wireless Sensor Networks"]}]


@pytest.mark.parametrize("korean, latin, fits", [
    ("김상훈", "Sanghoon Kim", True), ("김상훈", "Kim, Sang-Hoon", True), ("곽재헌", "Jaeheon Kwak", True),
    ("노병희", "Byeong-hee Roh", True), ("유리", "Ri Yu", True), ("손경아", "Kyung-Ah Sohn", True),
    ("김상훈", "Minsu Kim", False), ("김상훈", "Sanghoon Park", False), ("강경란", "Kang", False),
])
def test_hangul_names_match_romanised_authors(korean, latin, fits):
    from admission.openalex import romanization_fits

    assert romanization_fits(korean, latin) is fits


def test_hangul_name_is_linked_only_through_papers_on_the_official_page(monkeypatch):
    """No name search for 김용준 (same-name researchers at one university); a page paper decides."""
    from admission import openalex

    openalex._research.cache_clear()
    openalex._research_by_papers.cache_clear()
    monkeypatch.setattr(openalex, "institution_id", lambda *a: "I1")
    calls = []
    title = "NVMeVirt: A Versatile Software-defined Virtual NVMe Device"

    def fake_get(path, params):
        calls.append((path, params.get("search")))
        if path == "/works" and params.get("search"):
            return {"results": [{"id": "W1", "title": title, "authorships": [
                {"author": {"id": "A1", "display_name": "Sang-Hoon Kim"}},
                {"author": {"id": "A2", "display_name": "Minsu Kim"}},
                {"author": {"id": "A3", "display_name": "Sanghyun Kim"}}]}]}
        if path == "/authors/A1":
            return {"id": "A1", "affiliations": [{"institution": {"id": "I1"}}], "topics": [{"display_name": "Storage"}]}
        if path == "/authors/A3":
            return {"id": "A3", "affiliations": [{"institution": {"id": "I9"}}]}  # another university
        if path == "/works":
            return {"results": [{"id": "W2", "title": "Recent", "publication_year": 2025, "doi": "https://doi.org/x"}]}
        raise AssertionError(path)

    monkeypatch.setattr(openalex, "_get", fake_get)
    program = {"universityKey": "U", "universityName": "아주대학교", "country": "KR"}
    assert openalex.research_for("김용준", program, person={"name": "김용준"}) is None
    assert calls == []  # no papers on the page: nothing is searched by name

    found = openalex.research_for("김상훈", program, person={"name": "김상훈", "papers": [title]})
    assert found["source"] == "A1" and found["researchTopics"] == ["Storage"]
    assert not any(path == "/authors" for path, _ in calls)


@pytest.mark.parametrize("listed, title", [
    ("NVMeVirt: A Versatile Software-defined Virtual NVMe Device, USENIX FAST, 2023",
     "NVMeVirt: A Versatile Software-defined Virtual NVMe Device"),
    ("A Scalable Joint Routing and Scheduling Scheme for Large-scale Wireless Sensor Networks (2013)",
     "A Scalable Joint Routing and Scheduling Scheme for Large-scale Wireless Sensor Networks"),
    ("Rethinking Data Augmentation for Image Super-resolution: A Comprehensive Analysis and a New Strategy. CVPR (2020)",
     "Rethinking Data Augmentation for Image Super-resolution: A Comprehensive Analysis and a New Strategy"),
])
def test_paper_title_drops_venue_and_year(listed, title):
    from admission.openalex import paper_title

    assert paper_title(listed) == title


def test_openalex_research_that_does_not_fit_the_page_field_is_dropped():
    """A merged OpenAlex profile (networking professor + chemist of the same name) shows only fitting papers."""
    from admission.faculty import keep_matching_field

    professor = {"name": "김영훈", "field": "Networked Systems, Operating Systems, Clouds/Clusters"}
    found = {"researchTopics": ["Pharmacogenetics and Drug Metabolism", "Cloud Computing and Resource Management"],
             "recentWorks": [{"title": "Recent advancement in transition metal selenide electrodes"},
                             {"title": "PeRF: Preemption-enabled RDMA Framework for clusters"}]}
    kept = keep_matching_field(professor, found)
    assert kept["researchTopics"] == ["Cloud Computing and Resource Management"]
    assert [w["title"] for w in kept["recentWorks"]] == ["PeRF: Preemption-enabled RDMA Framework for clusters"]

    chemist_only = {"researchTopics": ["Pharmacogenetics and Drug Metabolism"],
                    "recentWorks": [{"title": "Transition metal selenide electrodes"}]}
    assert keep_matching_field(professor, chemist_only) is None
    # no field on the page (or only in Korean): nothing to compare, keep the latest three
    many = {"researchTopics": ["X"], "recentWorks": [{"title": str(i)} for i in range(8)]}
    assert len(keep_matching_field({"name": "A B", "field": "컴퓨터공학"}, many)["recentWorks"]) == 3


def test_openalex_stops_asking_once_the_daily_budget_is_used_up(monkeypatch):
    """A daily-budget 429 is not retried for minutes; later calls fail at once until the reset."""
    import io
    import urllib.error

    from admission import openalex

    calls = []

    def refuse(url, timeout):
        calls.append(url)
        body = b'{"reason": "daily_budget", "retryAfter": 600, "message": "Insufficient budget"}'
        raise urllib.error.HTTPError(url, 429, "Too Many Requests", {}, io.BytesIO(body))

    monkeypatch.setattr(openalex.urllib.request, "urlopen", refuse)
    monkeypatch.setattr(openalex, "_BUDGET_OUT", {"until": 0.0})
    for _ in range(2):
        with pytest.raises(openalex.BudgetExhausted):
            openalex._get("/works", {"search": "x"})
    assert len(calls) == 1
