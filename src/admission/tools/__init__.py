"""도구 정의 — docs/ARCHITECTURE.md 3절 표와 같은 시그니처·설명을 쓴다.

도구는 새 기능이 아니라 이미 있는 함수를 모델이 호출할 수 있게 잇는 연결 함수다.
모든 도구는 읽기 전용이다(쓰기 도구 없음 → 사용자 승인 대상 없음).
호출마다 구조화 로그(도구 이름, 입력 요약, 결과 개수, 소요 시간)를 남긴다.
"""

from __future__ import annotations

import json
import logging
import time
from functools import wraps

from admission.schemas import RequestContext


logger = logging.getLogger("admission.tools")

# 도구 이름 → (설명, 부작용). 설명 문장은 ARCHITECTURE.md 3절 표와 같아야 한다.
TOOL_SPECS: dict[str, dict[str, str]] = {
    "search_programs": {
        "description": "사용자 조건에 맞는 검증 후보 과정을 검증 데이터에서 찾고 요건을 판정한다",
        "side_effect": "read",
    },
    "get_evidence": {
        "description": "검증 후보마다 추천 근거가 될 공식 출처 근거 청크를 가져온다",
        "side_effect": "read",
    },
    "search_catalogue": {
        "description": "국가와 학위로 탐색용 대학 과정 목록을 읽는다(요건 판정 없음)",
        "side_effect": "read",
    },
    "explore_programmes_web": {
        "description": "검증 데이터에 없는 과정을 공식 대학 사이트 웹 검색으로 찾아 검증 전 결과로 돌려준다",
        "side_effect": "read",
    },
}


def _summary(value) -> object:
    if isinstance(value, RequestContext):
        return {
            "applicantType": value.applicantType,
            "preferredCountries": value.preferredCountries,
            "engineeringFields": value.engineeringFields,
        }
    if isinstance(value, (list, tuple, set)):
        return f"<{type(value).__name__} len={len(value)}>"
    if isinstance(value, dict):
        return f"<dict keys={sorted(value)[:5]}>"
    return value


def _result_size(result) -> int | None:
    if isinstance(result, dict) and "candidates" in result:
        return len(result["candidates"])
    if isinstance(result, (list, dict)):
        return len(result)
    return None


def logged_tool(name: str):
    """도구 호출을 구조화 로그로 남긴다(ARCHITECTURE.md 8절, evals 입력)."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            started = time.perf_counter()
            status = "ok"
            result = None
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as error:
                status = f"error:{type(error).__name__}"
                raise
            finally:
                logger.info(json.dumps({
                    "event": "tool_call",
                    "tool": name,
                    "args": [_summary(arg) for arg in args],
                    "kwargs": {key: _summary(val) for key, val in kwargs.items()},
                    "status": status,
                    "resultCount": _result_size(result),
                    "ms": round((time.perf_counter() - started) * 1000, 1),
                }, ensure_ascii=False, default=str))

        wrapper.tool_name = name
        wrapper.side_effect = TOOL_SPECS[name]["side_effect"]
        wrapper.__doc__ = TOOL_SPECS[name]["description"]
        return wrapper

    return decorator


@logged_tool("search_programs")
def search_programs(context: RequestContext) -> dict:
    from admission.official_sources import load_allowed_hosts
    from admission.recommend import recommend

    if not isinstance(context, RequestContext):
        context = RequestContext.model_validate(context)
    return recommend(context, allowed_hosts=load_allowed_hosts())


@logged_tool("get_evidence")
def get_evidence(
    candidates: list[dict],
    interests: list[str] | None = None,
) -> dict[str, list[dict]]:
    from admission.grounding import retrieve_candidate_evidence

    return retrieve_candidate_evidence(candidates, interests or [])


@logged_tool("search_catalogue")
def search_catalogue(country: str, degree: str | None = None, limit: int = 3) -> list[dict]:
    from admission.catalogue_routes import search_catalogue as _search

    return _search(country=country, degree=degree, limit=limit)["items"]


@logged_tool("explore_programmes_web")
def explore_programmes_web(
    context: RequestContext,
    exclude: set[str] | None = None,
    client=None,
) -> list[dict]:
    from admission.ai_exploration import explore_programmes

    if isinstance(context, RequestContext):
        context = context.model_dump()
    return explore_programmes(context, exclude or set(), client=client)


TOOLS = {
    "search_programs": search_programs,
    "get_evidence": get_evidence,
    "search_catalogue": search_catalogue,
    "explore_programmes_web": explore_programmes_web,
}
