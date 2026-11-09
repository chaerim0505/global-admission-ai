
import re
import unicodedata

from admission.requirement_extractor import AdmissionRequirements


REQUIREMENT_FIELDS = (
    "gpa",
    "english",
    "tuition",
    "scholarship",
    "deadline",
    "eligibility",
)


def normalize_text(text: str) -> str:
    """Normalize whitespace and Unicode for evidence comparison."""
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", "", text).casefold()


def validate_requirements(
    requirements: AdmissionRequirements,
    document_text: str,
    source_url: str,
) -> dict:
    """Check whether each extracted evidence quote exists in the PDF."""

    normalized_document = normalize_text(document_text)

    results = {}

    for field_name in REQUIREMENT_FIELDS:
        requirement = getattr(requirements, field_name)

        value = requirement.value
        evidence = requirement.evidenceText

        if not value or not evidence:
            status = "needs_check"
        elif normalize_text(evidence) in normalized_document:
            status = "evidence_found"
        else:
            status = "needs_check"

        results[field_name] = {
            "value": value,
            "evidenceText": evidence,
            "verificationStatus": status,
            "sourceUrl": source_url,
        }

    return {
        "university": requirements.university,
        "program": requirements.program,
        "degree": requirements.degree,
        "intake": requirements.intake,
        "requirements": results,
    }

