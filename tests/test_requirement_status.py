"""Requirement checklist rules (SPEC F02, AC5, AC6)."""

from admission.recommend_v2 import recommend, requirement_status

RATES = {"USD": 1.0, "KRW": 0.00072}
RULES = {"reach_if_gap_above": 10, "safety_if_gap_below": -10, "mix_when_possible": {}, "results_per_request": 5}


def status(checks, item):
    return next(c["status"] for c in checks if c["item"] == item)


def test_missing_data_is_needs_check_not_unmet():
    checks = requirement_status({"programId": "p"}, {"academicScore": 3.0, "maximumScore": 4.5, "gradingSystem": "gpa"})
    assert status(checks, "academic") == "needs_check"
    assert status(checks, "language") == "needs_check"
    assert status(checks, "deadline") == "needs_check"


def test_documented_gpa_and_language_give_met_or_unmet():
    program = {"minimumGpa": 3.0, "minimumGpaScale": 4.5,
               "languageRequirements": [{"testType": "IELTS", "minimumScore": 6.5}]}
    good = requirement_status(program, {"academicScore": 3.5, "maximumScore": 4.5, "gradingSystem": "gpa",
                                        "languageTestType": "IELTS", "languageTestScore": 7.0})
    bad = requirement_status(program, {"academicScore": 2.5, "maximumScore": 4.5, "gradingSystem": "gpa",
                                       "languageTestType": "IELTS", "languageTestScore": 6.0})
    assert status(good, "academic") == "met" and status(good, "language") == "met"
    assert status(bad, "academic") == "unmet" and status(bad, "language") == "unmet"


def test_different_gpa_scale_is_not_compared():
    checks = requirement_status({"minimumGpa": 3.0, "minimumGpaScale": 4.0},
                                {"academicScore": 3.9, "maximumScore": 4.5, "gradingSystem": "gpa"})
    assert status(checks, "academic") == "needs_check"


def test_recommend_excludes_documented_unmet_and_attaches_checklist():
    catalogue = [
        {"programId": "a", "universityKey": "u1", "universityName": "A", "country": "US", "degreeLevel": "master",
         "engineeringFields": ["computing"], "minimumGpa": 3.5, "minimumGpaScale": 4.0, "source": "team_verified"},
        {"programId": "b", "universityKey": "u2", "universityName": "B", "country": "US", "degreeLevel": "master",
         "engineeringFields": ["computing"], "source": "official_dataset"},
    ]
    ctx = {"preferredCountries": ["US"], "applicantType": "master", "engineeringFields": ["computing"],
           "academicScore": 3.0, "maximumScore": 4.0, "gradingSystem": "gpa"}
    out = recommend(ctx, catalogue, RATES, rules=RULES)
    assert [r["universityName"] for r in out["results"]] == ["B"]
    assert out["excluded"][0]["unmet"] == ["academic"]
    assert out["results"][0]["requirements"]
