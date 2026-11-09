from fastapi import FastAPI
from fastapi.responses import JSONResponse
from google.genai import errors as genai_errors
from httpx import TimeoutException
from pydantic import BaseModel, Field

from admission.clarification import build_follow_ups
from admission.context_merge import merge_context
from admission.official_sources import load_allowed_hosts
from admission.parser import parse_query
from admission.program_routes import router as program_router
from admission.recommend import recommend
from admission.schemas import RequestContext
from admission.scope import check_scope
from admission.validation import validate_request
from admission.auth import router as auth_router

app = FastAPI(title="Admission AI", version="0.2.0")
app.include_router(program_router)
app.include_router(auth_router)

class ParseRequest(BaseModel):
    """자연어 입력과 이전 대화 조건을 받는다."""

    text: str = Field(min_length=1, max_length=10000)
    previousContext: RequestContext | None = None


@app.get("/health")
def health():
    """서버 상태를 반환한다."""
    return {"status": "ok"}


@app.post("/validate")
def validate(context: RequestContext):
    """추천 실행에 필요한 입력을 검증한다."""
    errors = validate_request(context)

    if errors:
        return JSONResponse(
            status_code=422,
            content={"inputErrors": errors},
        )

    return {
        "valid": True,
        "context": context.model_dump(),
    }


@app.post("/parse")
def parse(request: ParseRequest):
    """자연어를 파싱하고 이전 조건과 병합한다."""
    if not request.text.strip():
        return JSONResponse(
            status_code=422,
            content={
                "inputErrors": [
                    {
                        "field": "text",
                        "problem": "missing",
                        "message": "입력 문장을 작성해 주세요.",
                    }
                ]
            },
        )

    try:
        update = parse_query(request.text)

    except genai_errors.APIError as error:
        if error.code == 429:
            status = 429
        elif error.code == 504:
            status = 504
        else:
            status = 503

        return JSONResponse(
            status_code=status,
            content={
                "error": {
                    "code": "model_request_failed",
                    "message": (
                        "AI 요청을 완료하지 못했습니다. "
                        "잠시 후 다시 시도해 주세요."
                    ),
                }
            },
        )

    except TimeoutException:
        return JSONResponse(
            status_code=504,
            content={
                "error": {
                    "code": "model_timeout",
                    "message": "AI 응답 시간이 초과되었습니다.",
                }
            },
        )

    if request.previousContext is None:
        context = update
    else:
        context = merge_context(request.previousContext, update)

    input_errors = validate_request(context)
    scope_notices = check_scope(context)

    return {
        "context": context.model_dump(),
        "readyForRecommendation": (
            not input_errors and not scope_notices
        ),
        "inputErrors": input_errors,
        "followUps": build_follow_ups(input_errors),
        "scopeNotices": scope_notices,
    }


@app.post("/recommend")
def recommend_programs(context: RequestContext):
    """공식 출처 허용 목록을 적용해 추천을 실행한다."""
    result = recommend(
        context,
        allowed_hosts=load_allowed_hosts(),
    )

    if "inputErrors" in result:
        return JSONResponse(
            status_code=422,
            content=result,
        )

    return result

from admission.catalogue_routes import router as catalogue_router
app.include_router(catalogue_router)


@app.post("/intake")
def intake(request: ParseRequest):
    """자연어 입력을 추천, 과정 목록, 근거 검색에 연결한다."""
    from admission.catalogue_routes import search_catalogue
    from admission.grounding import retrieve_candidate_evidence

    parsed = parse(request)
    if isinstance(parsed, JSONResponse):
        return parsed

    if not parsed["readyForRecommendation"]:
        return {"stage": "needs_input", **parsed}

    context = RequestContext.model_validate(parsed["context"])
    recommendation = recommend_programs(context)
    if isinstance(recommendation, JSONResponse):
        return recommendation

    countries = context.preferredCountries or ["KR", "US", "GB", "NL", "IE"]
    catalogue_items = []

    for country in dict.fromkeys(code.strip().upper() for code in countries):
        result = search_catalogue(
            country=country,
            degree=context.applicantType,
            limit=3,
        )
        catalogue_items.extend(result["items"])

    evidence_targets = [
        *recommendation["candidates"],
        *({"programId": item["candidate_id"]} for item in catalogue_items),
    ]
    evidence = retrieve_candidate_evidence(
        evidence_targets,
        context.interests or [],
    )

    return {
        "stage": "recommendation",
        "context": parsed["context"],
        "recommendation": recommendation,
        "catalogueMatches": catalogue_items,
        "retrievedEvidence": evidence,
        "groundingStatus": "references_found" if evidence else "needs_check",
    }

from admission.orchestrator import run_root_agent


@app.post("/agent/run")
def run_agent(request: ParseRequest):
    """Root Agent를 실행한다."""

    try:
        return run_root_agent(
            text=request.text,
            previous_context=request.previousContext,
        )

    except genai_errors.APIError as error:
        status = (
            429 if error.code == 429
            else 504 if error.code == 504
            else 503
        )
        return JSONResponse(
            status_code=status,
            content={
                "error": {
                    "code": "model_request_failed",
                    "message": "AI 요청을 완료하지 못했습니다.",
                }
            },
        )

    except TimeoutException:
        return JSONResponse(
            status_code=504,
            content={
                "error": {
                    "code": "model_timeout",
                    "message": "AI 응답 시간이 초과되었습니다.",
                }
            },
        )