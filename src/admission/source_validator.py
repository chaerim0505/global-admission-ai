from admission.program_schemas import Program
from admission.scope import SUPPORTED_COUNTRIES


def _has_source(item: dict | None) -> bool:
    return bool(item) and bool(item.get("sourceUrl")) and bool(
        item.get("checkedAt")
    )


def validate_candidates(
    candidates: list[dict],
    programs: list[Program],
) -> tuple[list[dict], list[dict[str, str]]]:
    """DB와 대조해 잘못 생성된 후보·출처 없는 항목을 제거한다 (AC1, AC3, AC4, AC7, AC12)."""
    by_id = {program.programId: program for program in programs}
    clean = []
    issues = []

    def issue(program_id: str, problem: str) -> None:
        issues.append({"programId": program_id, "problem": problem})

    for candidate in candidates:
        program_id = candidate.get("programId", "")
        program = by_id.get(program_id)

        if program is None:
            issue(program_id, "unknown_program")
            continue

        if (
            candidate.get("universityName") != program.universityName
            or candidate.get("programName") != program.programName
        ):
            issue(program_id, "name_mismatch")
            continue

        if candidate.get("country") not in SUPPORTED_COUNTRIES:
            issue(program_id, "unsupported_country")
            continue

        classification = candidate.get("fieldClassification") or {}
        if classification.get("status") != "included":
            issue(program_id, "not_included")
            continue

        if not _has_source(classification):
            issue(program_id, "missing_source:fieldClassification")
            continue

        requirements = []
        for requirement in candidate.get("requirements", []):
            if _has_source(requirement):
                requirements.append(requirement)
            else:
                issue(program_id, f'missing_source:{requirement.get("item")}')

        scholarships = []
        for scholarship in candidate.get("scholarships", []):
            if _has_source(scholarship):
                scholarships.append(scholarship)
            else:
                issue(program_id, "missing_source:scholarship")

        tuition = candidate.get("tuition")
        if tuition is not None:
            if not _has_source(tuition):
                issue(program_id, "missing_source:tuition")
                tuition = None
            elif program.tuition is None or (
                tuition.get("currency"),
                tuition.get("period"),
                tuition.get("amount"),
            ) != (
                program.tuition.currency,
                program.tuition.period,
                program.tuition.amount,
            ):
                issue(program_id, "tuition_mismatch")
                tuition = None

        deadline = candidate.get("applicationDeadline")
        if deadline is not None and not _has_source(deadline):
            issue(program_id, "missing_source:applicationDeadline")
            deadline = None

        clean.append({
            **candidate,
            "requirements": requirements,
            "scholarships": scholarships,
            "tuition": tuition,
            "applicationDeadline": deadline,
        })

    return clean, issues

def enforce_official_sources(
    candidates: list[dict],
    allowed_hosts: set[str],
) -> tuple[list[dict], list[dict[str, str]]]:
    """등록되지 않은 출처가 포함된 후보를 보류한다."""
    from admission.official_sources import is_allowed_source

    clean = []
    issues = []

    for candidate in candidates:
        entries = [
            candidate.get("fieldClassification"),
            candidate.get("tuition"),
            candidate.get("applicationDeadline"),
            *candidate.get("requirements", []),
            *candidate.get("scholarships", []),
        ]

        invalid = any(
            entry is not None
            and not is_allowed_source(
                str(entry.get("sourceUrl", "")),
                allowed_hosts,
            )
            for entry in entries
        )

        if invalid:
            issues.append({
                "programId": candidate["programId"],
                "problem": "unregistered_source",
            })
        else:
            clean.append(candidate)

    return clean, issues
