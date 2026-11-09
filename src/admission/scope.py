from admission.schemas import RequestContext


SUPPORTED_COUNTRIES = {"KR", "US", "GB", "NL", "IE"}

SCOPE_MESSAGE = (
    "현재 한국·미국·영국·네덜란드·아일랜드의 "
    "공학 분야 학위 과정만 지원합니다."
)


def check_scope(context: RequestContext) -> list[str]:
    notices = []

    unsupported = sorted({
        country.strip().upper()
        for country in (context.preferredCountries or [])
        if country.strip().upper() not in SUPPORTED_COUNTRIES
    })

    if unsupported:
        notices.append(
            f"지원 범위 밖의 희망 국가: {', '.join(unsupported)}. "
            f"{SCOPE_MESSAGE} 희망 국가를 확인해 주세요."
        )

    outside_requests = [
        item.strip()
        for item in (context.outOfScopeRequests or [])
        if item.strip()
    ]

    if outside_requests:
        notices.append(
            f"지원 범위 확인이 필요한 요청: "
            f"{'; '.join(outside_requests)}. "
            f"{SCOPE_MESSAGE}"
        )

    return notices