"""짧은 답변 해석 골든 테스트 — SPEC.md AC20.

케이스는 tests/harness/intake_followup_cases.yaml 에서 읽는다. 모델 응답은 케이스의
model_output 으로 고정하고, 실제 run_intake_agent 의 보정 규칙을 검사한다.
"""

from pathlib import Path

import pytest
import yaml

from admission.agents import intake_agent
from admission.agents.intake_agent import run_intake_agent
from admission.schemas import RequestContext


SPEC = yaml.safe_load(
    (Path(__file__).resolve().parent / "harness" / "intake_followup_cases.yaml").read_text(encoding="utf-8")
)
CASES = SPEC["cases"]
KNOWN_EXPECTED_KEYS = {"fields", "ready"}


def test_case_file_is_valid():
    ids = [case["id"] for case in CASES]
    assert len(ids) == len(set(ids))
    for case in CASES:
        assert {"id", "ac", "category", "previous", "answer", "model_output", "expected"} <= set(case)
        assert case["category"] in {"normal", "boundary", "forbidden"}
        # a misspelled key would otherwise pass without being checked
        assert not set(case["expected"]) - KNOWN_EXPECTED_KEYS


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_intake_followup_case(case, monkeypatch):
    previous = RequestContext.model_validate({**SPEC["base"], **case["previous"]})
    monkeypatch.setattr(
        intake_agent,
        "parse_query",
        lambda text, pending_questions=None: RequestContext.model_validate(case["model_output"]),
    )

    result = run_intake_agent(case["answer"], previous)

    expected = case["expected"]
    for field, value in expected["fields"].items():
        assert result["context"][field] == value, field
    if "ready" in expected:
        assert result["readyForRecommendation"] is expected["ready"]
