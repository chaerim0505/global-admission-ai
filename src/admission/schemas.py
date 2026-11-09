from typing import Literal

from pydantic import BaseModel, ConfigDict


DegreeLevel = Literal["undergraduate", "master", "phd"]

EngineeringField = Literal[
    "computing",
    "electrical_electronic",
    "mechanical",
    "civil_environmental",
    "chemical_materials",
    "industrial_systems",
    "aerospace",
    "biomedical",
    "other_engineering",
]

EducationLevel = Literal["high_school", "bachelor", "master"]

GradingSystem = Literal[
    "gpa",
    "percentage",
    "grade_rank",
    "total_score",
    "other",
]

LanguageTestType = Literal[
    "IELTS",
    "TOEFL_iBT",
    "Duolingo",
    "TOPIK",
    "other",
]

TuitionPeriod = Literal["semester", "year", "total"]


class RequestContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    applicantType: DegreeLevel | None = None
    currentEducationLevel: EducationLevel | None = None

    transcriptCountry: str | None = None
    nationality: str | None = None

    academicScore: float | None = None
    gradingSystem: GradingSystem | None = None
    maximumScore: float | None = None

    engineeringFields: list[EngineeringField] | None = None
    interests: list[str] | None = None
    preferredCountries: list[str] | None = None

    languageTestType: LanguageTestType | None = None
    languageTestScore: float | None = None

    maximumTuition: float | None = None
    tuitionCurrency: str | None = None
    tuitionPeriod: TuitionPeriod | None = None

    scholarshipRequired: bool | None = None
    professorMatchingRequired: bool | None = None

    # Preserve unsupported requests for scope validation.
    outOfScopeRequests: list[str] | None = None