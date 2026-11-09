import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent

scope = json.loads(
    (ROOT / "config" / "collection_scope.json").read_text(
        encoding="utf-8"
    )
)
programs = json.loads(
    (ROOT / "data" / "programs.json").read_text(
        encoding="utf-8"
    )
)

if not isinstance(programs, list):
    raise ValueError("programs.json must contain a list.")

seen_ids = set()
counts = Counter()
pending = 0

for program in programs:
    program_id = program["programId"]
    country = program["country"]
    degree = program["degreeLevel"]
    fields = program["engineeringFields"]

    if program_id in seen_ids:
        raise ValueError(f"Duplicate programId: {program_id}")
    seen_ids.add(program_id)

    if country not in scope["countries"]:
        raise ValueError(f"Unsupported country: {country}")

    if degree not in scope["degreeLevels"]:
        raise ValueError(f"Unsupported degree: {degree}")

    if not isinstance(fields, list) or not fields:
        raise ValueError(f"Engineering fields missing: {program_id}")

    for field in set(fields):
        if field not in scope["engineeringFields"]:
            raise ValueError(f"Unsupported engineering field: {field}")
        counts[(country, field, degree)] += 1

    if program.get("verificationStatus") != "verified":
        pending += 1

print(f"Total programs: {len(programs)}")
print(f"Pending verification: {pending}")
print("Counts include programs pending verification.")

for country in scope["countries"]:
    print(f"\n[{country}]")
    print("field: undergraduate / master / phd")

    for field in scope["engineeringFields"]:
        values = [
            str(counts[(country, field, degree)])
            for degree in scope["degreeLevels"]
        ]
        print(f"{field}: {' / '.join(values)}")