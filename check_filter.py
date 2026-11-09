from admission.program_filter import filter_programs
from admission.program_repository import load_programs
from admission.schemas import RequestContext


programs = load_programs()

cases = [
    ("IE master", ["IE"], "master", 1),
    ("US master", ["US"], "master", 0),
    ("IE undergraduate", ["IE"], "undergraduate", 0),
]

for label, countries, degree, expected in cases:
    context = RequestContext(
        preferredCountries=countries,
        applicantType=degree,
    )
    result = filter_programs(programs, context)

    assert len(result) == expected, (
        f"{label}: expected {expected}, got {len(result)}"
    )
    print(f"{label}: {len(result)}")

print("Filter checks passed.")