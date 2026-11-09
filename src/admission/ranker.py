BUDGET_ORDER = {"within": 0, "undetermined": 1, None: 1, "over": 2}


def rank_key(candidate: dict) -> tuple:
    """같은 입력에는 같은 순서. 동점이면 programId 오름차순 (SPEC 4.4)."""
    tuition = candidate.get("tuition") or {}
    needs_check = sum(
        1
        for requirement in candidate["requirements"]
        if requirement["status"] == "needs_check"
    )

    return (
        BUDGET_ORDER[tuition.get("budgetFit")],
        needs_check,
        candidate["programId"],
    )


def rank_candidates(candidates: list[dict]) -> list[dict]:
    return sorted(candidates, key=rank_key)
