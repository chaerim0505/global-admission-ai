from admission.schemas import RequestContext
from admission.validation import validate_request
from admission.scope import check_scope


def run_diagnosis_agent(context: RequestContext) -> dict:
    """
    사용자 프로필을 진단한다.

    - 필수 정보 확인
    - 학업 성적 확인
    - 영어 시험 정보 확인
    - 학비 및 장학금 선호 확인
    - 지원 범위 확인
    """

    input_errors = validate_request(context)
    scope_notices = check_scope(context)

    profile = {
        "degree": context.applicantType,
        "education": context.currentEducationLevel,
        "transcriptCountry": context.transcriptCountry,
        "academicScore": context.academicScore,
        "gradingSystem": context.gradingSystem,
        "maximumScore": context.maximumScore,
        "interests": context.interests or [],
        "preferredCountries": context.preferredCountries or [],
        "languageTestType": context.languageTestType,
        "languageTestScore": context.languageTestScore,
        "maximumTuition": context.maximumTuition,
        "scholarshipRequired": context.scholarshipRequired,
    }

    missing_optional = []

    if context.languageTestScore is None:
        missing_optional.append("language_test_score")

    if context.maximumTuition is None:
        missing_optional.append("maximum_tuition")

    if context.scholarshipRequired is None:
        missing_optional.append("scholarship_preference")

    return {
        "stage": "diagnosis",
        "profile": profile,
        "inputErrors": input_errors,
        "scopeNotices": scope_notices,
        "missingOptionalInformation": missing_optional,
        "readyForMatching": (
            not input_errors and not scope_notices
        ),
    }