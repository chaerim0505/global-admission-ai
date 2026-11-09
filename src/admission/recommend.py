from datetime import date

from admission.clarification import build_follow_ups
from admission.cost_matcher import build_scholarships, build_tuition
from admission.program_filter import filter_programs
from admission.program_repository import load_programs
from admission.program_schemas import Program
from admission.ranker import rank_candidates
from admission.reason_writer import write_reason
from admission.requirement_matcher import match_requirements
from admission.schemas import RequestContext
from admission.scope import SUPPORTED_COUNTRIES, check_scope
from admission.source_validator import (
    enforce_official_sources,
    validate_candidates,
)
from admission.validation import validate_request


FOLLOW_UP_TEXT = {
    "academic": "성적 요건은 공식 페이지에서 환산 기준을 확인해야 합니다.",
    "language": (
        "어학 요건을 확인해야 합니다. 어학 점수를 입력하지 않았거나 "
        "공식 요건을 아직 확보하지 못했습니다."
    ),
    "deadline": "모집 마감일이 확인되지 않은 과정이 있습니다.",
    "tuition": "학비 정보를 확보하지 못한 과정이 있습니다.",
    "scholarship": "장학금 정보를 확보하지 못한 과정이 있습니다.",
    "scholarship_check": (
        "국적 제한이 명시되지 않았거나 웹에서 찾은 장학금은 "
        "공식 페이지에서 확인해야 합니다."
    ),
}

NO_RESULT_TEXT = (
    "현재 확보하고 검증한 데이터에서 조건에 맞는 후보를 "
    "반환하지 못했습니다. 조건은 자동으로 완화하지 않았습니다. "
    "희망 국가, 학위, 공학 세부 분야, 최대 학비를 확인하거나 "
    "변경해 다시 검색할 수 있습니다."
)


def _pick_field(program: Program, context: RequestContext) -> str:
    """과정의 분류 중 요청 분야와 일치하는 값을 선택한다."""
    requested = set(context.engineeringFields or [])
    matched = sorted(requested.intersection(program.engineeringFields))
    return matched[0] if matched else program.engineeringFields[0]


def _search_context(
    context: RequestContext,
) -> RequestContext | None:
    """요청한 지원 국가만 유지하고 다른 국가로 대체하지 않는다."""
    if context.preferredCountries is None:
        return context

    supported = [
        country.strip().upper()
        for country in context.preferredCountries
        if country.strip().upper() in SUPPORTED_COUNTRIES
    ]

    if not supported:
        return None

    return context.model_copy(
        update={"preferredCountries": supported}
    )


def build_candidate(
    program: Program,
    context: RequestContext,
    today: date,
) -> dict:
    """과정 데이터를 판정 결과와 함께 후보 응답으로 구성한다."""
    deadline = program.applicationDeadline

    return {
        "programId": program.programId,
        "universityName": program.universityName,
        "country": program.country,
        "programName": program.programName,
        "degreeLevel": program.degreeLevel,
        "engineeringField": _pick_field(program, context),
        "topics": program.topics,
        "fieldClassification": {
            "status": program.fieldClassification.status,
            "reason": program.fieldClassification.reason,
            "sourceUrl": str(program.fieldClassification.sourceUrl),
            "checkedAt": str(program.fieldClassification.checkedAt),
        },
        "reason": "",
        "requirements": match_requirements(program, context),
        "tuition": build_tuition(program, context),
        "applicationDeadline": {
            "date": None if deadline is None else str(deadline),
            "intake": program.intake,
            "sourceUrl": str(program.sourceUrl),
            "checkedAt": str(program.checkedAt),
        },
        "scholarships": build_scholarships(program, today),
    }


def _follow_ups(
    candidates: list[dict],
    context: RequestContext,
) -> list[str]:
    """후보에서 추가 확인이 필요한 항목을 모은다."""
    keys = []

    for candidate in candidates:
        for requirement in candidate["requirements"]:
            if requirement["status"] == "needs_check":
                keys.append(requirement["item"])

        deadline = candidate.get("applicationDeadline")
        if deadline is None or deadline.get("date") is None:
            keys.append("deadline")

        if candidate["tuition"] is None:
            keys.append("tuition")

        if context.scholarshipRequired and not candidate["scholarships"]:
            keys.append("scholarship")

        if any(
            scholarship["status"] == "needs_check"
            for scholarship in candidate["scholarships"]
        ):
            keys.append("scholarship_check")

    return [
        FOLLOW_UP_TEXT.get(
            key,
            f"{key} 요건은 공식 안내와 사용자 정보를 추가 확인해야 합니다.",
        )
        for key in dict.fromkeys(keys)
    ]


def recommend(
    context: RequestContext,
    programs: list[Program] | None = None,
    today: date | None = None,
    allowed_hosts: set[str] | None = None,
) -> dict:
    """입력을 검증하고 과정 후보와 근거를 반환한다."""
    today = today or date.today()

    input_errors = validate_request(context)
    if input_errors:
        return {
            "inputErrors": input_errors,
            "followUps": [
                item["question"]
                for item in build_follow_ups(input_errors)
            ],
        }

    scope_notices = check_scope(context)
    search_context = _search_context(context)

    if search_context is None:
        found = []
        programs = [] if programs is None else programs
    else:
        programs = load_programs() if programs is None else programs
        found = filter_programs(programs, search_context)

    candidates = []
    excluded = []

    for program in found:
        if (
            program.applicationDeadline is not None
            and program.applicationDeadline < today
        ):
            excluded.append({
                "programId": program.programId,
                "reason": "deadline_passed",
                "detail": (
                    f"모집 마감일 {program.applicationDeadline}이 "
                    "지났습니다."
                ),
            })
            continue

        candidate = build_candidate(program, context, today)
        unmet = [
            requirement
            for requirement in candidate["requirements"]
            if requirement["status"] == "unmet"
        ]

        if unmet:
            excluded.append({
                "programId": program.programId,
                "reason": "requirement_unmet",
                "detail": "; ".join(
                    requirement["evidence"]
                    for requirement in unmet
                ),
            })
            continue

        candidates.append(candidate)

    candidates, issues = validate_candidates(candidates, programs)

    if allowed_hosts is not None:
        candidates, official_issues = enforce_official_sources(
            candidates,
            allowed_hosts,
        )
        issues.extend(official_issues)

    candidates = rank_candidates(candidates)

    for candidate in candidates:
        candidate["reason"] = write_reason(candidate, context)

    follow_ups = _follow_ups(candidates, context)

    if any(
        issue["problem"] == "unregistered_source"
        for issue in issues
    ):
        follow_ups.append(
            "공식 출처 등록 확인이 필요한 과정이 있어 "
            "일부 후보를 보류했습니다."
        )

    if not candidates and search_context is not None:
        follow_ups.append(NO_RESULT_TEXT)

    return {
        "candidates": candidates,
        "excluded": excluded,
        "scopeNotices": scope_notices,
        "followUps": follow_ups,
        "validationIssues": issues,
    }