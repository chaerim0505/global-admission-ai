import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from admission.program_schemas import Program  # noqa: E402
from admission.schemas import RequestContext  # noqa: E402


TODAY = date(2026, 11, 5)
SOURCE = "https://www.example.edu/test-program"


def make_program(**overrides) -> Program:
    """테스트 전용 가상 과정. 실제 대학 데이터가 아니다."""
    data = {
        "programId": "test-kr-cs-master",
        "universityName": "Test University",
        "country": "KR",
        "programName": "MS in Computer Science",
        "degreeLevel": "master",
        "engineeringFields": ["computing"],
        "topics": ["Artificial Intelligence", "Databases"],
        "fieldClassification": {
            "status": "included",
            "reason": "공과대학 소속 컴퓨터공학 석사 과정",
            "sourceUrl": SOURCE,
            "checkedAt": "2026-11-04",
        },
        "intake": "2027-03",
        "minimumGpa": 3.0,
        "minimumGpaScale": 4.0,
        "applicationDeadline": "2026-12-01",
        "languageRequirements": [
            {
                "testType": "IELTS",
                "minimumScore": 6.5,
                "sourceUrl": SOURCE,
                "checkedAt": "2026-11-04",
            }
        ],
        "tuition": {
            "amount": 5000000,
            "currency": "KRW",
            "period": "semester",
            "sourceUrl": SOURCE,
            "checkedAt": "2026-11-04",
        },
        "scholarships": [],
        "sourceUrl": SOURCE,
        "checkedAt": "2026-11-04",
    }
    data.update(overrides)
    return Program.model_validate(data)


@pytest.fixture
def context() -> RequestContext:
    return RequestContext(
        applicantType="master",
        currentEducationLevel="bachelor",
        transcriptCountry="MM",
        nationality="MM",
        academicScore=3.4,
        gradingSystem="gpa",
        maximumScore=4.0,
        engineeringFields=["computing"],
        interests=["Artificial Intelligence"],
        preferredCountries=["KR"],
        languageTestType="IELTS",
        languageTestScore=7.0,
        maximumTuition=6000000,
        tuitionCurrency="KRW",
        tuitionPeriod="semester",
    )
