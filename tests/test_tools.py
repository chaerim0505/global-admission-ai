"""도구 계약 테스트 — 강의 6 B절 계약 조건, docs/ARCHITECTURE.md 3절.

기존 함수의 정확성(골든 케이스가 검사)이 아니라 연결 함수의 계약만 검사한다.
"""

import copy
import inspect
import json
import logging
import re
from pathlib import Path

import pytest

from admission import tools
from admission.schemas import RequestContext


ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE = ROOT / "docs" / "ARCHITECTURE.md"
PROGRAMS = ROOT / "data" / "programs.json"
EVIDENCE = ROOT / "data" / "evidence_chunks.json"

CONTEXT = RequestContext(
    applicantType="master",
    currentEducationLevel="bachelor",
    transcriptCountry="MM",
    academicScore=3.4,
    gradingSystem="gpa",
    maximumScore=4.0,
    engineeringFields=["computing"],
    interests=["AI"],
    preferredCountries=["IE"],
)


def test_tool_set_matches_architecture_table():
    """코드의 도구 이름·설명·부작용이 ARCHITECTURE.md 3절 표와 같다."""
    text = ARCHITECTURE.read_text(encoding="utf-8")
    rows = re.findall(r"^\| (\w+) \| `[^`]*` \| ([^|]+) \| ([^|]+) \|$", text, re.M)
    table = {name: (desc.strip(), effect.strip()) for name, desc, effect in rows}

    assert set(table) == set(tools.TOOLS)
    for name, spec in tools.TOOL_SPECS.items():
        description, effect = table[name]
        assert description == spec["description"], name
        assert effect.startswith("없음(읽기)"), name


def test_every_tool_is_read_only():
    """쓰기 도구가 없으므로 사용자 승인 없이 실행되는 쓰기 경로도 없다."""
    for name, func in tools.TOOLS.items():
        assert func.side_effect == "read", name


def test_search_programs_takes_request_context():
    params = inspect.signature(tools.search_programs).parameters
    assert params["context"].annotation in (RequestContext, "RequestContext")


def test_search_programs_does_not_change_state():
    before_data = PROGRAMS.read_bytes()
    before_context = copy.deepcopy(CONTEXT.model_dump())

    result = tools.search_programs(CONTEXT)

    assert PROGRAMS.read_bytes() == before_data
    assert CONTEXT.model_dump() == before_context
    assert all(c["country"] == "IE" for c in result["candidates"])


def test_get_evidence_does_not_change_state():
    candidates = [{"programId": "galway-1mai1-2027"}]
    before_candidates = copy.deepcopy(candidates)
    before_data = EVIDENCE.read_bytes() if EVIDENCE.exists() else None

    result = tools.get_evidence(candidates, ["AI"])

    assert candidates == before_candidates
    if before_data is not None:
        assert EVIDENCE.read_bytes() == before_data
    assert set(result) <= {"galway-1mai1-2027"}


def test_tool_calls_are_logged(caplog):
    with caplog.at_level(logging.INFO, logger="admission.tools"):
        tools.search_programs(CONTEXT)

    events = [json.loads(record.getMessage()) for record in caplog.records]
    call = next(event for event in events if event["tool"] == "search_programs")
    assert call["event"] == "tool_call"
    assert call["status"] == "ok"
    assert call["resultCount"] is not None
    assert "ms" in call


def test_failed_tool_call_is_logged(caplog):
    class Broken:
        class models:
            @staticmethod
            def generate_content(**kwargs):
                raise RuntimeError("boom")

    pytest.importorskip("google.genai")
    with caplog.at_level(logging.INFO, logger="admission.tools"):
        with pytest.raises(RuntimeError):
            tools.explore_programmes_web(CONTEXT, client=Broken())

    events = [json.loads(record.getMessage()) for record in caplog.records]
    assert events[-1]["status"] == "error:RuntimeError"


def test_rag_config_drives_retrieval():
    """검색 파라미터는 config/rag.yaml에서 온다(코드에 박지 않음)."""
    from admission.rag_config import load_rag_config, min_evidence, retrieval_top_k

    config = load_rag_config()
    for section in ("source", "chunking", "embedding", "store", "retrieval", "constraints", "observability"):
        assert section in config, section
    assert retrieval_top_k() == config["retrieval"]["top_k"]
    assert min_evidence() >= 1
    assert config["constraints"]["verified_candidates_only"] is True


def test_grounding_marks_candidates_without_evidence():
    """근거가 min_evidence 미만인 후보는 근거 부족으로 표시한다."""
    from admission.agents.grounding_agent import run_grounding_agent

    result = run_grounding_agent({"candidates": [{"programId": "no-evidence-program"}]})

    assert result["groundingStatus"] == "needs_check"
    assert result["candidatesLackingEvidence"] == ["no-evidence-program"]
