from conftest import TODAY, make_program

from admission.recommend import build_candidate
from admission.source_validator import validate_candidates


def candidate_for(context, program):
    return build_candidate(program, context, TODAY)


def test_unknown_program_removed(context):
    # AC3: a programId that is not in the data is dropped.
    fake = candidate_for(context, make_program(programId="made-up"))
    clean, issues = validate_candidates([fake], [make_program()])
    assert clean == []
    assert issues[0]["problem"] == "unknown_program"


def test_name_mismatch_removed(context):
    candidate = candidate_for(context, make_program())
    candidate["universityName"] = "Invented University"
    clean, issues = validate_candidates([candidate], [make_program()])
    assert clean == []
    assert issues[0]["problem"] == "name_mismatch"


def test_requirement_without_source_removed(context):
    candidate = candidate_for(context, make_program())
    candidate["requirements"][0]["sourceUrl"] = ""
    clean, issues = validate_candidates([candidate], [make_program()])
    assert len(clean[0]["requirements"]) == 1
    assert issues[0]["problem"].startswith("missing_source")


def test_changed_tuition_removed(context):
    candidate = candidate_for(context, make_program())
    candidate["tuition"]["amount"] = 1
    clean, issues = validate_candidates([candidate], [make_program()])
    assert clean[0]["tuition"] is None
    assert issues[0]["problem"] == "tuition_mismatch"


def test_valid_candidate_kept(context):
    candidate = candidate_for(context, make_program())
    clean, issues = validate_candidates([candidate], [make_program()])
    assert len(clean) == 1
    assert issues == []
