from admission.program_schemas import Program
from admission.schemas import RequestContext


def filter_programs(
    programs: list[Program],
    context: RequestContext,
) -> list[Program]:
    countries = {
        country.strip().upper()
        for country in context.preferredCountries or []
        if country.strip()
    }
    fields = set(context.engineeringFields or [])

    candidates = []

    for program in programs:
        # Only programs confirmed as engineering can be recommended (AC12).
        if program.fieldClassification.status != "included":
            continue

        if countries and program.country not in countries:
            continue

        if (
            context.applicantType is not None
            and program.degreeLevel != context.applicantType
        ):
            continue

        if fields and not fields.intersection(program.engineeringFields):
            continue

        candidates.append(program)

    return candidates