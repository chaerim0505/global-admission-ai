"""Evals 러너 자체 검증 — 오답을 넣으면 실패로 판정하는가(강의 7, 러너 위임 수용 조건)."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("run_evals", ROOT / "evals" / "run_evals.py")
run_evals = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_evals)

CASES = {case["id"]: case for case in run_evals.load_cases()}


def test_evalset_is_valid_and_large_enough():
    assert len(CASES) >= 20
    categories = {case["category"] for case in CASES.values()}
    assert {"constraint", "conflict", "clarify", "out_of_scope", "injection", "hallucination"} <= categories


def test_recommendation_grader_rejects_invented_and_wrong_country():
    wrong = {
        "candidates": [{
            "programId": "invented-program", "country": "CA", "degreeLevel": "master",
            "fieldClassification": {"sourceUrl": "", "checkedAt": ""},
            "requirements": [], "scholarships": [], "tuition": None,
        }],
        "excluded": [], "scopeNotices": [], "followUps": [],
    }
    failures = run_evals.grade_recommendation(CASES["e01"], wrong)
    text = " ".join(failures)
    assert "허용 밖 국가" in text
    assert "데이터에 없는 programId" in text
    assert "galway-1mai1-2027 누락" in text


def test_intake_grader_rejects_wrong_field_and_injection():
    wrong = {"context": {"transcriptCountry": None, "preferredCountries": ["KR"]},
             "readyForRecommendation": True}
    assert run_evals.grade_intake(CASES["e19"], wrong)

    injected = {"context": {"preferredCountries": ["GB"], "applicantType": "master",
                            "engineeringFields": ["mechanical"], "interests": ["MIT"]}}
    assert any("MIT" in f for f in run_evals.grade_intake(CASES["e16"], injected))

    invented_field = {"context": {"engineeringFields": ["computing"], "interests": ["AI"],
                                  "applicantType": "master", "preferredCountries": ["NL"]}}
    assert run_evals.grade_intake(CASES["e13"], invented_field)


def test_exploration_grader_rejects_rule_violations():
    wrong = [
        {"universityName": "A", "country": "CA", "sourceUrl": "http://a", "verificationStatus": "verified"},
        {"universityName": "B", "country": "NL", "sourceUrl": "https://b", "verificationStatus": "ai_suggested",
         "requirements": []},
    ]
    failures = " ".join(run_evals.grade_exploration(CASES["e23"], wrong))
    assert "요청 밖 국가" in failures
    assert "https 링크 없음" in failures
    assert "status" in failures
    assert "요건 판정 포함" in failures


def test_correct_outputs_pass():
    right = [{"universityName": "TU Delft", "country": "NL", "sourceUrl": "https://tudelft.nl",
              "verificationStatus": "ai_suggested"}]
    assert run_evals.grade_exploration(CASES["e23"], right) == []
