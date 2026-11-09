from datetime import date
from typing import Literal

from admission.program_schemas import Program, Scholarship, Tuition
from admission.schemas import RequestContext


BudgetFit = Literal["within", "over", "undetermined"]


def compare_tuition(tuition: Tuition, context: RequestContext) -> BudgetFit:
    """같은 통화·기간일 때만 예산과 비교한다 (AC7).

    수혜가 확정되지 않은 장학금은 빼지 않는다 (AC17).
    """
    if context.maximumTuition is None:
        return "undetermined"

    currency = (context.tuitionCurrency or "").strip().upper()

    if (tuition.currency.upper(), tuition.period) != (
        currency,
        context.tuitionPeriod,
    ):
        return "undetermined"

    return "within" if tuition.amount <= context.maximumTuition else "over"


def build_tuition(
    program: Program,
    context: RequestContext,
) -> dict | None:
    tuition = program.tuition

    if tuition is None:
        return None

    return {
        "amount": tuition.amount,
        "currency": tuition.currency,
        "period": tuition.period,
        "budgetFit": compare_tuition(tuition, context),
        "sourceUrl": str(tuition.sourceUrl),
        "checkedAt": str(tuition.checkedAt),
    }


def scholarship_status(scholarship: Scholarship) -> str:
    # Web results and unstated nationality rules stay needs_check (AC5).
    if scholarship.origin == "web_search":
        return "needs_check"
    if scholarship.nationalityRestriction is None:
        return "needs_check"
    return "listed"


def build_scholarships(program: Program, today: date) -> list[dict]:
    results = []

    for scholarship in program.scholarships:
        if scholarship.deadline is not None and scholarship.deadline < today:
            continue

        results.append({
            "name": scholarship.name,
            "amount": scholarship.amount,
            "eligibility": scholarship.eligibility,
            "nationalityRestriction": scholarship.nationalityRestriction,
            "deadline": (
                None
                if scholarship.deadline is None
                else str(scholarship.deadline)
            ),
            "origin": scholarship.origin,
            "status": scholarship_status(scholarship),
            "sourceUrl": str(scholarship.sourceUrl),
            "checkedAt": str(scholarship.checkedAt),
        })

    return results
