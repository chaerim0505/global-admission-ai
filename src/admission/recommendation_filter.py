from admission.recommendation_schemas import ProgramRecord
from admission.schemas import RequestContext


SUPPORTED_COUNTRIES = {"KR", "US", "GB", "NL", "IE"}


def filter_program_records(
    records: list[ProgramRecord],
    context: RequestContext,
) -> list[ProgramRecord]:
    """명시된 조건과 공학 포함 판정에 맞는 후보만 반환한다."""
    countries = {
        value.strip().upper()
        for value in context.preferredCountries or []
        if value.strip()
    }

    # 범위 밖 국가를 다른 국가로 대체하지 않는다.
    if countries - SUPPORTED_COUNTRIES:
        return []

    fields = set(context.engineeringFields or [])
    candidates = []

    for record in records:
        if record.fieldClassification.status != "included":
            continue

        if countries and record.country not in countries:
            continue

        if (
            context.applicantType is not None
            and record.degreeLevel != context.applicantType
        ):
            continue

        if fields and record.engineeringField not in fields:
            continue

        candidates.append(record)

    return sorted(candidates, key=lambda record: record.programId)