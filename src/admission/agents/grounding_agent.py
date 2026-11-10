from admission.tools import get_evidence


def run_grounding_agent(
    recommendation: dict,
    interests: list[str] | None = None,
) -> dict:
    """
    추천 후보에 대한 근거를 검색한다.

    주의:
    근거가 검색되었다는 사실만으로
    입학 요건이 공식 검증된 것은 아니다.
    """

    candidates = recommendation.get("candidates", [])

    if not candidates:
        return {
            "stage": "grounding",
            "groundingStatus": "no_candidates",
            "retrievedEvidence": [],
            "validationIssues": recommendation.get(
                "validationIssues", []
            ),
        }

    evidence = get_evidence(
        candidates,
        interests or [],
    )

    from admission.rag_config import min_evidence

    # 근거 부족 감지(config/rag.yaml retrieval.min_evidence): 근거가 모자란 후보를 밝힌다.
    needed = min_evidence()
    lacking = [
        candidate["programId"]
        for candidate in candidates
        if len(evidence.get(candidate.get("programId"), [])) < needed
    ]

    if not evidence:
        status = "needs_check"
    elif lacking:
        status = "partial"
    else:
        status = "references_found"

    return {
        "stage": "grounding",
        "groundingStatus": status,
        "candidatesLackingEvidence": lacking,
        "retrievedEvidence": evidence,
        "validationIssues": recommendation.get(
            "validationIssues", []
        ),
    }
