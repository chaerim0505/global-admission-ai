from conftest import make_program

from admission.requirement_matcher import match_academic, match_language


def test_gpa_met(context):
    result = match_academic(make_program(), context)
    assert result["status"] == "met"
    assert result["sourceUrl"] and result["checkedAt"]


def test_gpa_unmet(context):
    context.academicScore = 2.5
    assert match_academic(make_program(), context)["status"] == "unmet"


def test_gpa_different_scale_needs_check(context):
    # No official conversion between 4.5 and 4.0 scales (AC5).
    context.maximumScore = 4.5
    assert match_academic(make_program(), context)["status"] == "needs_check"


def test_percentage_needs_check(context):
    context.gradingSystem = "percentage"
    context.academicScore = 85
    context.maximumScore = None
    assert match_academic(make_program(), context)["status"] == "needs_check"


def test_text_only_requirement_needs_check(context):
    program = make_program(
        minimumGpa=None,
        minimumGpaScale=None,
        academicRequirementText="First Class Honours or equivalent.",
    )
    result = match_academic(program, context)
    assert result["status"] == "needs_check"
    assert "First Class Honours" in result["evidence"]


def test_missing_language_score_is_not_unmet(context):
    context.languageTestType = None
    context.languageTestScore = None
    assert match_language(make_program(), context)["status"] == "needs_check"


def test_language_met_and_unmet(context):
    assert match_language(make_program(), context)["status"] == "met"
    context.languageTestScore = 6.0
    assert match_language(make_program(), context)["status"] == "unmet"


def test_other_test_type_needs_check(context):
    context.languageTestType = "TOEFL_iBT"
    context.languageTestScore = 100
    assert match_language(make_program(), context)["status"] == "needs_check"


def test_language_not_collected_needs_check(context):
    program = make_program(languageRequirements=None)
    assert match_language(program, context)["status"] == "needs_check"


def test_language_not_required_is_skipped(context):
    program = make_program(languageRequirements=[])
    assert match_language(program, context) is None
