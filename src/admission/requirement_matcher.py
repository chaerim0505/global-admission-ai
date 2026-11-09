from typing import Literal

from admission.program_schemas import Program
from admission.schemas import RequestContext


RequirementStatus = Literal["met", "unmet", "needs_check"]


def _result(
    item: str,
    status: RequirementStatus,
    evidence: str,
    source_url: object,
    checked_at: object,
) -> dict[str, str]:
    return {
        "item": item,
        "status": status,
        "evidence": evidence,
        "sourceUrl": str(source_url),
        "checkedAt": str(checked_at),
    }


def match_academic(
    program: Program,
    context: RequestContext,
) -> dict[str, str]:
    """성적 요건 판정. 공식 환산 기준이 없으면 needs_check (AC5)."""
    source, checked = program.sourceUrl, program.checkedAt

    if program.minimumGpa is None:
        if program.academicRequirementText:
            return _result(
                "academic",
                "needs_check",
                f"공식 요건 원문: {program.academicRequirementText}",
                source,
                checked,
            )
        return _result(
            "academic",
            "needs_check",
            "공식 성적 요건을 아직 확보하지 못했습니다.",
            source,
            checked,
        )

    same_scale = (
        context.gradingSystem == "gpa"
        and program.minimumGpaScale is not None
        and context.maximumScore == program.minimumGpaScale
    )

    if not same_scale or context.academicScore is None:
        return _result(
            "academic",
            "needs_check",
            (
                f"최소 GPA {program.minimumGpa}/{program.minimumGpaScale}. "
                "입력한 성적 체계와 비교할 공식 환산 기준이 없습니다."
            ),
            source,
            checked,
        )

    status = (
        "met" if context.academicScore >= program.minimumGpa else "unmet"
    )

    return _result(
        "academic",
        status,
        (
            f"최소 GPA {program.minimumGpa}/{program.minimumGpaScale}, "
            f"입력 GPA {context.academicScore}/{context.maximumScore}"
        ),
        source,
        checked,
    )


def match_language(
    program: Program,
    context: RequestContext,
) -> dict[str, str] | None:
    """어학 요건 판정. 요구하지 않는 과정이면 None (비교하지 않음)."""
    requirements = program.languageRequirements

    if requirements is None:
        return _result(
            "language",
            "needs_check",
            "공식 어학 요건을 아직 확보하지 못했습니다.",
            program.sourceUrl,
            program.checkedAt,
        )

    if not requirements:
        return None

    accepted = ", ".join(
        f"{req.testType} {req.minimumScore}" for req in requirements
    )
    first = requirements[0]

    if context.languageTestType is None or context.languageTestScore is None:
        # Missing score is not a failure (AC5).
        return _result(
            "language",
            "needs_check",
            f"인정 시험: {accepted}. 어학 점수가 입력되지 않았습니다.",
            first.sourceUrl,
            first.checkedAt,
        )

    for req in requirements:
        if req.testType == context.languageTestType:
            status = (
                "met"
                if context.languageTestScore >= req.minimumScore
                else "unmet"
            )
            return _result(
                "language",
                status,
                (
                    f"{req.testType} 최소 {req.minimumScore}, "
                    f"입력 {context.languageTestScore}"
                ),
                req.sourceUrl,
                req.checkedAt,
            )

    return _result(
        "language",
        "needs_check",
        (
            f"인정 시험: {accepted}. "
            f"{context.languageTestType} 인정 여부를 확인해야 합니다."
        ),
        first.sourceUrl,
        first.checkedAt,
    )


def match_requirements(
    program: Program,
    context: RequestContext,
) -> list[dict[str, str]]:
    results = [match_academic(program, context)]

    language = match_language(program, context)
    if language is not None:
        results.append(language)

    return results
