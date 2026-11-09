import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from admission.recommendation_repository import load_program_records


def make_record() -> dict:
    """외부 호출 없이 사용할 테스트 전용 레코드를 만든다."""
    evidence = {
        "sourceUrl": "https://example.org/test-only",
        "checkedAt": "2026-11-04",
        "excerpt": "Synthetic evidence for automated tests only.",
    }

    return {
        "programId": "test-program-001",
        "universityName": "Test University",
        "country": "KR",
        "programName": "Test Engineering Programme",
        "degreeLevel": "master",
        "engineeringField": "computing",
        "topics": ["Artificial Intelligence"],
        "fieldClassification": {
            "status": "included",
            "reason": "Synthetic classification for testing.",
            "evidence": evidence,
        },
        "evidence": evidence,
    }


def write_records(tmp_path: Path, records: list[dict]) -> Path:
    """테스트 임시 폴더에 JSON 파일을 저장한다."""
    path = tmp_path / "programs.json"
    path.write_text(
        json.dumps(records, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def test_load_valid_record(tmp_path: Path) -> None:
    """정상 데이터를 읽고 미확보 항목을 보존한다."""
    path = write_records(tmp_path, [make_record()])

    records = load_program_records(path)

    assert len(records) == 1
    assert records[0].engineeringField == "computing"
    assert records[0].tuition is None
    assert records[0].admissionRequirements is None


def test_reject_duplicate_ids(tmp_path: Path) -> None:
    """중복 과정 ID를 거부한다."""
    record = make_record()
    path = write_records(tmp_path, [record, record])

    with pytest.raises(ValueError, match="Duplicate programId"):
        load_program_records(path)


def test_reject_missing_evidence_date(tmp_path: Path) -> None:
    """근거의 확인 날짜가 없으면 거부한다."""
    record = make_record()
    del record["evidence"]["checkedAt"]
    path = write_records(tmp_path, [record])

    with pytest.raises(ValidationError):
        load_program_records(path)


def test_reject_unsupported_country(tmp_path: Path) -> None:
    """지원 범위 밖의 과정 국가를 거부한다."""
    record = make_record()
    record["country"] = "CA"
    path = write_records(tmp_path, [record])

    with pytest.raises(ValidationError):
        load_program_records(path)