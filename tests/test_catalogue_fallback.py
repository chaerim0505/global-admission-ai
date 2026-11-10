"""채팅 탐색 목록이 결과 탭과 같은 과정 목록을 쓰는지 (배포 환경에는 카탈로그 DB가 없음)."""

from admission.orchestrator import search_catalogue_file
from admission.schemas import RequestContext


def test_demo_scenario_finds_ajou():
    context = RequestContext(
        applicantType="undergraduate",
        engineeringFields=["computing"],
        preferredCountries=["KR"],
    )
    items = search_catalogue_file(context)

    names = {item["universityName"] for item in items}
    assert "Ajou University" in names
    assert len(items) == 5
    assert all(item["country"] == "KR" for item in items)
    assert all(item["degreeLevel"] == "undergraduate" for item in items)


def test_only_requested_country_and_degree():
    context = RequestContext(
        applicantType="master",
        engineeringFields=["mechanical"],
        preferredCountries=["GB"],
    )
    for item in search_catalogue_file(context):
        assert item["country"] == "GB"
        assert item["degreeLevel"] == "master"


def test_unsupported_country_returns_nothing():
    context = RequestContext(applicantType="master", preferredCountries=["CA"])
    assert search_catalogue_file(context) == []
