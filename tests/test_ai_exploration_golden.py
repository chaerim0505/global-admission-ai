"""AI 탐색 결과(검증 전) 계약 테스트 — SPEC.md AC19.

케이스는 tests/harness/ai_exploration_cases.yaml 에서 읽는다. 케이스를 코드에 복사하지 않는다.
"""

from datetime import date
from pathlib import Path

import pytest
import yaml

from admission.ai_exploration import (
    ExplorationTimeout,
    STATUS,
    build_prompt,
    explore_programmes,
    normalize_items,
    parse_json_list,
)


CASES_PATH = (
    Path(__file__).resolve().parent / "harness" / "ai_exploration_cases.yaml"
)
CASES = yaml.safe_load(CASES_PATH.read_text(encoding="utf-8"))


def test_case_file_is_valid():
    assert CASES, "케이스가 비어 있음"
    ids = [case["id"] for case in CASES]
    assert len(ids) == len(set(ids))
    for case in CASES:
        assert {"id", "ac", "context", "model_output", "expected"} <= set(case)


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_ai_exploration_case(case):
    items = parse_json_list(case["model_output"])
    result = normalize_items(
        items,
        case["context"],
        set(case.get("exclude") or []),
        today=date(2026, 11, 11),
    )
    expected = case["expected"]
    # a misspelled key would otherwise pass without being checked
    assert not set(expected) - {"count", "universities", "absent", "countries_only", "all_status"}
    names = {item["universityName"] for item in result}
    if "all_status" in expected:
        assert all(item["verificationStatus"] == expected["all_status"] for item in result)

    if "count" in expected:
        assert len(result) == expected["count"]
    for name in expected.get("universities", []):
        assert name in names
    for name in expected.get("absent", []):
        assert name not in names
    if "countries_only" in expected:
        assert {item["country"] for item in result} <= set(expected["countries_only"])

    # AC19 공통 규칙: 모든 항목에 적용
    for item in result:
        assert item["verificationStatus"] == STATUS
        assert item["sourceUrl"].startswith("https://")
        assert item["programId"].startswith("ai_")
        assert "eligibility" not in item
        assert "requirements" not in item


class _FakeResponse:
    def __init__(self, text):
        self.text = text


class _FakeModels:
    def __init__(self, text):
        self.text = text
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeResponse(self.text)


class _FakeClient:
    def __init__(self, text):
        self.models = _FakeModels(text)


def test_explore_programmes_uses_google_search_and_filters(monkeypatch):
    case = CASES[0]
    client = _FakeClient(case["model_output"])

    result = explore_programmes(case["context"], set(), client=client)

    assert [item["universityName"] for item in result] == [
        "Delft University of Technology"
    ]
    call = client.models.calls[0]
    assert "Do not judge admission eligibility" in call["contents"]


class _TimeoutThenAnswer(_FakeModels):
    """First call times out (504), later calls answer."""

    def __init__(self, text, failures):
        super().__init__(text)
        self.failures = failures

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) <= self.failures:
            raise RuntimeError("504 DEADLINE_EXCEEDED")
        return _FakeResponse(self.text)


def test_explore_programmes_retries_once_after_timeout():
    case = CASES[0]
    client = _FakeClient(case["model_output"])
    client.models = _TimeoutThenAnswer(case["model_output"], failures=1)

    result = explore_programmes(case["context"], set(), client=client)

    assert len(client.models.calls) == 2
    assert [item["universityName"] for item in result] == ["Delft University of Technology"]


def test_explore_programmes_reports_timeout_after_retry():
    case = CASES[0]
    client = _FakeClient(case["model_output"])
    client.models = _TimeoutThenAnswer(case["model_output"], failures=2)

    with pytest.raises(ExplorationTimeout):
        explore_programmes(case["context"], set(), client=client)
    assert len(client.models.calls) == 2


def test_explore_programmes_does_not_retry_other_errors():
    case = CASES[0]
    client = _FakeClient(case["model_output"])

    def broken(**kwargs):
        client.models.calls.append(kwargs)
        raise ValueError("bad request")

    client.models.generate_content = broken
    with pytest.raises(ValueError):
        explore_programmes(case["context"], set(), client=client)
    assert len(client.models.calls) == 1


def test_prompt_asks_only_for_the_programme_page():
    prompt = build_prompt(CASES[0]["context"], set())
    assert "tuitionAmount" not in prompt
    assert "ieltsOverall" not in prompt
    assert "Do not judge admission eligibility" in prompt


def test_explore_programmes_drops_thinking_setting_if_model_rejects_it():
    case = CASES[0]
    client = _FakeClient(case["model_output"])
    answer = client.models.generate_content

    def first_rejects(**kwargs):
        if not client.models.calls:
            client.models.calls.append(kwargs)
            raise RuntimeError("400 INVALID_ARGUMENT thinking_level")
        return answer(**kwargs)

    client.models.generate_content = first_rejects
    result = explore_programmes(case["context"], set(), client=client)

    assert len(client.models.calls) == 2
    assert [item["universityName"] for item in result] == ["Delft University of Technology"]
