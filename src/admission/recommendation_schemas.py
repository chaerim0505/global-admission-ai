from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from admission.schemas import DegreeLevel, EngineeringField, TuitionPeriod


class StrictModel(BaseModel):
    """정의하지 않은 필드 입력을 거부한다."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        allow_inf_nan=False,
    )


class Evidence(StrictModel):
    """개별 정보의 공식 근거와 적용 범위를 저장한다."""

    sourceUrl: HttpUrl
    checkedAt: date
    excerpt: str = Field(min_length=1)
    admissionCycle: str | None = None
    applicantCategory: str | None = None


class FieldClassification(StrictModel):
    """공학 분야 포함 여부와 분류 근거를 저장한다."""

    status: Literal["included", "excluded", "needs_review"]
    reason: str = Field(min_length=1)
    evidence: Evidence


class AdmissionRequirement(StrictModel):
    """공식 입학 요건을 사용자 판정 결과와 분리해 저장한다."""

    requirementId: str = Field(min_length=1)
    item: Literal[
        "education",
        "major",
        "prerequisite",
        "academic",
        "language",
        "nationality",
        "other",
    ]
    description: str = Field(min_length=1)
    mandatory: bool
    evidence: Evidence


class Tuition(StrictModel):
    """학비의 원문 금액·통화·기간과 근거를 저장한다."""

    amount: float = Field(ge=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    period: TuitionPeriod
    evidence: Evidence


class ApplicationDeadline(StrictModel):
    """입학 마감일과 적용 모집 시점을 저장한다."""

    deadline: date | None = None
    intake: str | None = None
    evidence: Evidence


class Scholarship(StrictModel):
    """장학금 공고를 수혜 확정 여부와 구분해 저장한다."""

    scholarshipId: str = Field(min_length=1)
    name: str = Field(min_length=1)
    amount: str | None = None
    eligibility: str | None = None
    nationalityRestriction: str | None = None
    deadline: date | None = None
    evidence: Evidence


class ProgramRecord(StrictModel):
    """5개국 과정과 항목별 근거를 공통 형식으로 저장한다."""

    programId: str = Field(min_length=1)
    universityName: str = Field(min_length=1)
    country: Literal["KR", "US", "GB", "NL", "IE"]
    programName: str = Field(min_length=1)
    degreeLevel: DegreeLevel
    engineeringField: EngineeringField
    topics: list[str] = Field(min_length=1)
    fieldClassification: FieldClassification
    evidence: Evidence

    admissionRequirements: list[AdmissionRequirement] | None = None
    tuition: Tuition | None = None
    applicationDeadline: ApplicationDeadline | None = None
    scholarships: list[Scholarship] | None = None