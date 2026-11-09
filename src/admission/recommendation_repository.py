from pathlib import Path

from pydantic import TypeAdapter

from admission.recommendation_schemas import ProgramRecord


def load_program_records(path: Path) -> list[ProgramRecord]:
    """과정 데이터를 검증해 읽고 중복 ID를 거부한다."""
    records = TypeAdapter(list[ProgramRecord]).validate_json(
        path.read_text(encoding="utf-8")
    )

    seen_ids: set[str] = set()

    for record in records:
        if record.programId in seen_ids:
            raise ValueError(
                f"Duplicate programId: {record.programId}"
            )
        seen_ids.add(record.programId)

    return records