from typing import Literal

from admission.recommendation_filter import filter_program_records
from admission.recommendation_schemas import ProgramRecord
from admission.schemas import RequestContext


def make_record(
    program_id: str,
    country: str = "KR",
    field: str = "computing",
    degree: str = "master",
    status: Literal[
        "included", "excluded", "needs_review"
    ] = "included",
) -> ProgramRecord:
    """테스트 전용 과정과 근거를 만든다."""
    evidence = {
        "sourceUrl": "https://example.org/test-only",
        "checkedAt": "2026-11-04",
        "excerpt": "Synthetic evidence for testing only.",
    }

    return ProgramRecord.model_validate({
        "programId": program_id,
        "universityName": "Test University",
        "country": country,
        "programName": "Test Programme",
        "degreeLevel": degree,
        "engineeringField": field,
        "topics": ["Test topic"],
        "fieldClassification": {
            "status": status,
            "reason": "Test classification",
            "evidence": evidence,
        },
        "evidence": evidence,
    })


def test_filter_country_degree_and_field() -> None:
    """요청한 국가·학위·분야만 반환한다."""
    records = [
        make_record("match"),
        make_record("wrong-country", country="US"),
        make_record("wrong-degree", degree="undergraduate"),
        make_record("wrong-field", field="mechanical"),
    ]
    context = RequestContext(
        applicantType="master",
        preferredCountries=["KR"],
        engineeringFields=["computing"],
    )

    result = filter_program_records(records, context)

    assert [record.programId for record in result] == ["match"]


def test_only_included_records() -> None:
    """검토 대기와 제외 과정을 반환하지 않는다."""
    records = [
        make_record("included"),
        make_record("review", status="needs_review"),
        make_record("excluded", status="excluded"),
    ]

    result = filter_program_records(records, RequestContext())

    assert [record.programId for record in result] == ["included"]


def test_no_country_preference_searches_all_five() -> None:
    """희망 국가가 없으면 5개국 후보를 유지한다."""
    countries = ["KR", "US", "GB", "NL", "IE"]
    records = [
        make_record(country, country=country)
        for country in countries
    ]
    context = RequestContext(
        applicantType="master",
        nationality="MM",
        transcriptCountry="MM",
    )

    result = filter_program_records(records, context)

    assert {record.country for record in result} == set(countries)


def test_unsupported_country_does_not_fallback() -> None:
    """범위 밖 국가 요청을 다른 국가로 대체하지 않는다."""
    context = RequestContext(preferredCountries=["CA"])

    result = filter_program_records(
        [make_record("korea")],
        context,
    )

    assert result == []


def test_order_is_stable() -> None:
    """원본 순서가 달라도 ID 순서가 동일하다."""
    records = [make_record("b"), make_record("a")]
    context = RequestContext()

    first = filter_program_records(records, context)
    second = filter_program_records(list(reversed(records)), context)

    assert [record.programId for record in first] == ["a", "b"]
    assert first == second