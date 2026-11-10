from admission.clarification import build_follow_ups
from admission.context_merge import merge_context
from admission.parser import parse_query
from admission.schemas import RequestContext
from admission.scope import check_scope
from admission.validation import validate_request


COUNTRY_ALIASES = {
    "KR": {
        "kr", "kor", "korea", "south korea", "republic of korea", "rok",
        "한국", "대한민국", "남한",
    },
    "US": {
        "us", "usa", "united states", "united states of america", "america",
        "미국", "미합중국",
    },
    "GB": {
        "gb", "uk", "united kingdom", "great britain", "britain", "england",
        "scotland", "wales", "영국", "잉글랜드",
    },
    "NL": {"nl", "netherlands", "the netherlands", "holland", "네덜란드", "홀란드"},
    "IE": {"ie", "ireland", "republic of ireland", "아일랜드"},
    "MM": {"mm", "myanmar", "burma", "미얀마", "버마"},
}

ANSWER_SUFFIXES = ("입니다", "이에요", "예요", "에요", "이요", "요")


def country_code(text: str) -> str | None:
    """Turn a bare country answer such as 'KR' or '한국' into a code."""
    value = text.strip().strip(".!?").strip().casefold()
    value = " ".join(value.replace(".", "").split())
    if value.startswith("the "):
        value = value[4:]
    for suffix in ANSWER_SUFFIXES:
        if value.endswith(suffix) and len(value) > len(suffix):
            value = value[: -len(suffix)].strip()
            break

    for code, aliases in COUNTRY_ALIASES.items():
        if value in aliases:
            return code

    if len(value) == 2 and value.isascii() and value.isalpha():
        return value.upper()

    return None


def apply_pending_answer(
    update: RequestContext,
    text: str,
    pending_fields: list[str],
) -> RequestContext:
    """A bare country answer to the transcript question fills that field."""
    if "transcriptCountry" not in pending_fields or update.transcriptCountry:
        return update

    code = country_code(text)
    if code is None:
        return update

    countries = update.preferredCountries
    if countries and [c.strip().upper() for c in countries] == [code]:
        # The model guessed the wrong field for this short answer.
        countries = None

    return update.model_copy(
        update={"transcriptCountry": code, "preferredCountries": countries}
    )


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

    pending = (
        build_follow_ups(validate_request(previous_context))
        if previous_context is not None
        else []
    )
    update = parse_query(
        text,
        pending_questions=[item["question"] for item in pending] or None,
    )
    update = apply_pending_answer(
        update, text, [item["field"] for item in pending]
    )

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