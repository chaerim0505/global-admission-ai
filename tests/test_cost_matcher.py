from conftest import SOURCE, TODAY, make_program

from admission.cost_matcher import build_scholarships, build_tuition


def scholarship(**overrides) -> dict:
    data = {
        "name": "Test Scholarship",
        "amount": "등록금 100%",
        "nationalityRestriction": "제한 없음",
        "deadline": "2026-12-15",
        "sourceUrl": SOURCE,
        "checkedAt": "2026-11-04",
    }
    data.update(overrides)
    return data


def test_within_budget(context):
    assert build_tuition(make_program(), context)["budgetFit"] == "within"


def test_over_budget(context):
    context.maximumTuition = 4000000
    assert build_tuition(make_program(), context)["budgetFit"] == "over"


def test_different_currency_is_undetermined(context):
    # AC7: never convert without an official rate.
    context.tuitionCurrency = "USD"
    context.maximumTuition = 100000
    assert build_tuition(make_program(), context)["budgetFit"] == "undetermined"


def test_different_period_is_undetermined(context):
    context.tuitionPeriod = "year"
    assert build_tuition(make_program(), context)["budgetFit"] == "undetermined"


def test_no_budget_is_undetermined(context):
    context.maximumTuition = None
    assert build_tuition(make_program(), context)["budgetFit"] == "undetermined"


def test_tuition_keeps_original_units(context):
    tuition = build_tuition(make_program(), context)
    assert (tuition["amount"], tuition["currency"], tuition["period"]) == (
        5000000,
        "KRW",
        "semester",
    )


def test_scholarship_not_subtracted(context):
    # AC17: a full-tuition scholarship must not change the tuition.
    context.maximumTuition = 1000000
    program = make_program(scholarships=[scholarship()])
    tuition = build_tuition(program, context)
    assert tuition["amount"] == 5000000
    assert tuition["budgetFit"] == "over"


def test_unstated_nationality_needs_check():
    program = make_program(
        scholarships=[scholarship(nationalityRestriction=None)]
    )
    assert build_scholarships(program, TODAY)[0]["status"] == "needs_check"


def test_web_search_scholarship_needs_check():
    program = make_program(scholarships=[scholarship(origin="web_search")])
    assert build_scholarships(program, TODAY)[0]["status"] == "needs_check"


def test_expired_scholarship_dropped():
    program = make_program(scholarships=[scholarship(deadline="2026-10-01")])
    assert build_scholarships(program, TODAY) == []
