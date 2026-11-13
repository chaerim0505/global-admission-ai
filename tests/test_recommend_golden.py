from conftest import TODAY

from admission.evaluator import load_cases, run


def test_golden_cases_pass_on_current_data():
    report = run(load_cases(), today=TODAY)
    failed = [row for row in report["cases"] if not row["passed"]]
    assert failed == []
    assert report["validationIssues"] == 0
