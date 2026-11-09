from conftest import TODAY, make_program

from admission.recommend import recommend
from admission.schemas import RequestContext


def run(context, programs):
    return recommend(context, programs=programs, today=TODAY)


def test_input_errors_stop_recommendation():
    result = run(RequestContext(applicantType="master"), [make_program()])
    assert "inputErrors" in result
    assert "candidates" not in result


def test_only_requested_country(context):
    programs = [
        make_program(),
        make_program(programId="test-us-cs", country="US"),
    ]
    result = run(context, programs)
    assert {c["country"] for c in result["candidates"]} == {"KR"}


def test_unsupported_country_is_not_replaced(context):
    # AC13: CA only -> no search in other countries.
    context.preferredCountries = ["CA"]
    result = run(context, [make_program()])
    assert result["candidates"] == []
    assert result["scopeNotices"]


def test_mixed_countries_search_supported_only(context):
    context.preferredCountries = ["KR", "CA"]
    result = run(context, [make_program()])
    assert len(result["candidates"]) == 1
    assert result["scopeNotices"]


def test_needs_review_program_not_recommended(context):
    # AC12
    program = make_program(
        fieldClassification={
            "status": "needs_review",
            "reason": "융합 과정 검토 중",
            "sourceUrl": "https://www.example.edu/x",
            "checkedAt": "2026-11-04",
        }
    )
    assert run(context, [program])["candidates"] == []


def test_deadline_passed_excluded(context):
    # AC6
    program = make_program(applicationDeadline="2026-10-01")
    result = run(context, [program])
    assert result["candidates"] == []
    assert result["excluded"][0]["reason"] == "deadline_passed"


def test_unmet_requirement_excluded(context):
    # AC6
    context.academicScore = 2.0
    result = run(context, [make_program()])
    assert result["candidates"] == []
    assert result["excluded"][0]["reason"] == "requirement_unmet"


def test_no_result_does_not_relax(context):
    # AC9
    context.applicantType = "phd"
    result = run(context, [make_program()])
    assert result["candidates"] == []
    assert any("완화하지 않았습니다" in f for f in result["followUps"])


def test_every_item_has_source(context):
    # AC4
    candidate = run(context, [make_program()])["candidates"][0]
    items = [
        candidate["fieldClassification"],
        candidate["tuition"],
        candidate["applicationDeadline"],
        *candidate["requirements"],
    ]
    assert all(item["sourceUrl"] and item["checkedAt"] for item in items)


def test_non_engineering_major_not_rejected(context):
    # AC14: nationality or transcript country outside the 5 is fine.
    context.nationality = "VN"
    context.transcriptCountry = "VN"
    assert len(run(context, [make_program()])["candidates"]) == 1


def test_deterministic_order(context):
    programs = [
        make_program(programId="b-program"),
        make_program(programId="a-program"),
        make_program(programId="c-over", tuition={
            "amount": 9000000,
            "currency": "KRW",
            "period": "semester",
            "sourceUrl": "https://www.example.edu/c",
            "checkedAt": "2026-11-04",
        }),
    ]
    first = [c["programId"] for c in run(context, programs)["candidates"]]
    second = [c["programId"] for c in run(context, programs[::-1])["candidates"]]
    assert first == second == ["a-program", "b-program", "c-over"]


def test_reason_does_not_claim_eligible_with_needs_check(context):
    context.languageTestType = None
    context.languageTestScore = None
    candidate = run(context, [make_program()])["candidates"][0]
    assert "확정하지 않았습니다" in candidate["reason"]
