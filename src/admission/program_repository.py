from pathlib import Path

from pydantic import TypeAdapter

from admission.program_schemas import Program


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "programs.json"


def load_programs(path: Path | None = None) -> list[Program]:
    data_path = DEFAULT_DATA_PATH if path is None else path

    programs = TypeAdapter(list[Program]).validate_json(
        data_path.read_text(encoding="utf-8")
    )

    seen_ids: set[str] = set()

    for program in programs:
        if program.programId in seen_ids:
            raise ValueError(
                f"Duplicate programId: {program.programId}"
            )
        seen_ids.add(program.programId)

    return programs
    