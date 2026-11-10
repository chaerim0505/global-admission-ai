from fastapi import HTTPException
from admission.agents.intake_agent import run_intake_agent
from admission.agents.diagnosis_agent import run_diagnosis_agent
from admission.agents.matching_agent import run_matching_agent
from admission.agents.grounding_agent import run_grounding_agent
from admission.schemas import RequestContext


def run_root_agent(
    text: str,
    previous_context: RequestContext | None = None,
) -> dict:
    """전체 Admission AI Agent 실행 흐름을 관리한다."""

    # 1. Intake Agent
    intake = run_intake_agent(text, previous_context)
    context = RequestContext.model_validate(intake["context"])

    if not intake["readyForRecommendation"]:
        return {
            "stage": "needs_input",
            "context": intake["context"],
            "inputErrors": intake["inputErrors"],
            "followUps": intake["followUps"],
            "scopeNotices": intake["scopeNotices"],
        }

    # 2. Diagnosis Agent
    diagnosis = run_diagnosis_agent(context)

    if not diagnosis["readyForMatching"]:
        return {
            "stage": "needs_input",
            "context": context.model_dump(),
            "diagnosis": diagnosis,
            "inputErrors": diagnosis["inputErrors"],
            "scopeNotices": diagnosis["scopeNotices"],
        }

        # 3. Matching Agent
    matching = run_matching_agent(context)

    # 4. Catalogue Search
    # 검증된 추천 후보와 별도로 탐색용 대학 목록 조회
    from admission.tools import search_catalogue

    countries = context.preferredCountries or [
        "KR", "US", "GB", "NL", "IE"
    ]

    catalogue_items = []

    for country in dict.fromkeys(
        code.strip().upper() for code in countries
    ):
        try:
            items = search_catalogue(
                country=country,
                degree=context.applicantType,
                limit=3,
            )
        except HTTPException:
            # 카탈로그 DB가 없어도 추천 결과는 반환한다.
            continue
        catalogue_items.extend(items)

    # 5. Grounding Agent
    grounding = run_grounding_agent(
        matching["recommendation"],
        interests=context.interests,
    )

    # 6. Final Result
    return {
        "stage": "recommendation",
        "context": context.model_dump(),
        "diagnosis": diagnosis,
        "recommendation": matching["recommendation"],
        "catalogueMatches": catalogue_items,
        "retrievedEvidence": grounding["retrievedEvidence"],
        "groundingStatus": grounding["groundingStatus"],
        "candidatesLackingEvidence": grounding.get("candidatesLackingEvidence", []),
    }
