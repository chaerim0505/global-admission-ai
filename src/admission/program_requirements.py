from typing import Literal
from pydantic import BaseModel, Field

VerificationStatus = Literal["evidence_found", "needs_check"]

class RequirementEvidence(BaseModel):
    value: str | None = None
    evidenceText: str | None = None
    sourceUrl: str | None = None
    pageNumber: int | None = None
    verificationStatus: VerificationStatus = "needs_check"

class ProgramAdmissionRequirements(BaseModel):
    programId: str
    university: str
    department: str
    major: str
    degree: str
    intake: str

    admissionAvailable: bool | None = None
    languageRequirementType: str | None = None
    priorConsultationRequired: bool | None = None

    gpa: RequirementEvidence = Field(default_factory=RequirementEvidence)
    english: RequirementEvidence = Field(default_factory=RequirementEvidence)
    tuition: RequirementEvidence = Field(default_factory=RequirementEvidence)
    scholarship: list[RequirementEvidence] = Field(default_factory=list)
    deadline: RequirementEvidence = Field(default_factory=RequirementEvidence)
    eligibility: RequirementEvidence = Field(default_factory=RequirementEvidence)
