from admission.clarification import build_follow_ups
from admission.context_merge import merge_context
from admission.parser import parse_query
from admission.schemas import RequestContext
from admission.scope import check_scope
from admission.validation import validate_request


def run_intake_agent(
    text: str,
    previous_context: RequestContext | None = None,
) -> dict:
    """사용자 입력을 분석하고 추천에 필요한 조건을 수집한다."""

    if not text.strip():
        return {
            "stage": "needs_input",
            "context": (
                previous_context.model_dump()
                if previous_context is not None
                else RequestContext().model_dump()
            ),
            "readyForRecommendation": False,
            "inputErrors": [
                {
                    "field": "text",
                    "problem": "missing",
                    "message": "입력 문장을 작성해 주세요.",
                }
            ],
            "followUps": [
                {
                    "field": "text",
                    "question": "지원하고 싶은 대학이나 전공을 알려주세요.",
                }
            ],
            "scopeNotices": [],
        }

    update = parse_query(text)

    if previous_context is None:
        context = update
    else:
        context = merge_context(previous_context, update)

    input_errors = validate_request(context)
    scope_notices = check_scope(context)

    ready = not input_errors and not scope_notices

    return {
        "stage": "ready" if ready else "needs_input",
        "context": context.model_dump(),
        "readyForRecommendation": ready,
        "inputErrors": input_errors,
        "followUps": build_follow_ups(input_errors),
        "scopeNotices": scope_notices,
    }