import os

from admission.schemas import RequestContext


BUDGET_TEXT = {
    "within": "학비가 입력한 예산 안에 있습니다.",
    "over": "학비가 입력한 예산을 넘습니다.",
    "undetermined": (
        "학비의 통화나 기간이 입력과 달라 예산 적합성을 확정하지 않았습니다."
    ),
}


def template_reason(candidate: dict, context: RequestContext) -> str:
    """응답에 이미 있는 값만 사용한다. 새 사실을 만들지 않는다."""
    parts = [
        f'{candidate["universityName"]}의 {candidate["programName"]}는 '
        f'{candidate["engineeringField"]} 분야 과정입니다.'
    ]

    interests = {i.casefold() for i in context.interests or []}
    topics = [
        topic
        for topic in candidate.get("topics", [])
        if any(word in topic.casefold() for word in interests)
    ]
    if topics:
        parts.append(f'관심 분야와 관련된 주제: {", ".join(topics)}.')

    statuses = [r["status"] for r in candidate["requirements"]]
    met = statuses.count("met")
    check = statuses.count("needs_check")
    parts.append(f"요건 {len(statuses)}개 중 충족 {met}개, 확인 필요 {check}개.")

    tuition = candidate.get("tuition")
    if tuition is None:
        parts.append("학비 정보는 아직 확보하지 못했습니다.")
    else:
        parts.append(BUDGET_TEXT[tuition["budgetFit"]])

    if check:
        parts.append("확인 필요 항목이 있어 지원 가능 여부는 확정하지 않았습니다.")

    return " ".join(parts)


def write_reason(candidate: dict, context: RequestContext) -> str:
    # Gemini wording is opt-in; the template is the safe default.
    if os.getenv("REASON_WRITER") != "gemini":
        return template_reason(candidate, context)

    try:
        from admission.gemini_reason import gemini_reason

        return gemini_reason(candidate, template_reason(candidate, context))
    except Exception:
        return template_reason(candidate, context)
