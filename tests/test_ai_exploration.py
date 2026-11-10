"""AI 탐색 결과(검증 전) 계약 테스트 — SPEC.md AC19.

케이스는 tests/harness/ai_exploration_cases.yaml 에서 읽는다. 케이스를 코드에 복사하지 않는다.
"""

from datetime import date
from pathlib import Path

import pytest
import yaml

from admission.ai_exploration import (
    STATUS,
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
    names = {item["universityName"] for item in result}

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
    pytest.importorskip("google.genai")
    case = CASES[0]
    client = _FakeClient(case["model_output"])

    result = explore_programmes(case["context"], set(), client=client)

    assert [item["universityName"] for item in result] == [
        "Delft University of Technology"
    ]
    call = client.models.calls[0]
    assert "Do not judge admission eligibility" in call["contents"]
