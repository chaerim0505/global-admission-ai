from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from admission.schemas import (
    DegreeLevel,
    EngineeringField,
    LanguageTestType,
    TuitionPeriod,
)


class SourcedModel(BaseModel):
    """공식 출처와 확인일을 반드시 갖는 데이터 (AC4)."""

    model_config = ConfigDict(extra="forbid")

    sourceUrl: HttpUrl
    checkedAt: date


class FieldClassification(SourcedModel):
    # needs_review / excluded 과정은 추천하지 않는다 (AC12).
    status: Literal["included", "excluded", "needs_review"]
    reason: str = Field(min_length=1)


class LanguageRequirement(SourcedModel):
    testType: LanguageTestType
    minimumScore: float = Field(ge=0)


class Tuition(SourcedModel):
    # 통화와 기간은 원문 그대로 보존한다 (AC7).
    amount: float = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    period: TuitionPeriod


class Scholarship(SourcedModel):
    name: str = Field(min_length=1)
    amount: str | None = None
    eligibility: str | None = None
    # None = 공고에 국적 제한 여부가 명시되지 않음 → needs_check (AC5).
    nationalityRestriction: str | None = None
    deadline: date | None = None
    # web_search = Scholarship Research Agent가 찾은 후보 (항상 needs_check).
    origin: Literal["database", "web_search"] = "database"


class Program(BaseModel):
    model_config = ConfigDict(extra="forbid")

    programId: str = Field(min_length=1)
    universityName: str = Field(min_length=1)
    country: Literal["KR", "US", "GB", "NL", "IE"]
    programName: str = Field(min_length=1)
    degreeLevel: DegreeLevel
    engineeringFields: list[EngineeringField] = Field(min_length=1)
    topics: list[str] = Field(min_length=1)
    fieldClassification: FieldClassification

    intake: str | None = Field(
        default=None,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
    )
    academicRequirementText: str | None = None
    minimumGpa: float | None = Field(default=None, ge=0)
    # minimumGpa의 만점. 사용자 만점과 같을 때만 비교한다.
    minimumGpaScale: float | None = Field(default=None, gt=0)
    applicationDeadline: date | None = None

    # None = 아직 확보하지 못함 → needs_check
    # []   = 공식적으로 요구하지 않음 → 비교하지 않음
    languageRequirements: list[LanguageRequirement] | None = None

    tuition: Tuition | None = None
    scholarships: list[Scholarship] = Field(default_factory=list)

    sourceUrl: HttpUrl
    checkedAt: date
    verificationStatus: Literal["needs_check", "verified"] = "needs_check"
