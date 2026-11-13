"""저장소 표준 위치의 스키마·프롬프트가 코드와 어긋나지 않는지 확인한다."""

import json
from pathlib import Path

from admission.parser import PROMPT_PATH, SYSTEM_PROMPT
from admission.program_schemas import Program
from admission.schemas import RequestContext

SCHEMAS = Path(__file__).resolve().parents[1] / "src" / "admission" / "schemas"


def test_schema_files_match_models():
    """schema.json을 고치지 않고 모델만 바꾸면 실패한다(다시 생성할 것)."""
    for name, model in [("request_context", RequestContext), ("program", Program)]:
        saved = json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8"))
        assert saved == model.model_json_schema(), name


def test_parse_prompt_is_loaded_from_file():
    assert PROMPT_PATH.name == "parse_query.md"
    assert "RequestContext" in SYSTEM_PROMPT
    assert "[직전 질문]" in SYSTEM_PROMPT
    assert not SYSTEM_PROMPT.startswith("#")
