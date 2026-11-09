from admission.grounding import retrieve_candidate_evidence


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

    evidence = retrieve_candidate_evidence(
        candidates,
        interests or [],
    )

    return {
        "stage": "grounding",
        "groundingStatus": (
            "references_found"
            if evidence
            else "needs_check"
        ),
        "retrievedEvidence": evidence,
        "validationIssues": recommendation.get(
            "validationIssues", []
        ),
    }