from admission.schemas import RequestContext


def validate_request(context: RequestContext) -> list[dict[str, str]]:
    errors = []

    def add_error(field: str, problem: str, message: str):
        errors.append({
            "field": field,
            "problem": problem,
            "message": message,
        })

    required_fields = [
        "applicantType",
        "currentEducationLevel",
        "transcriptCountry",
        "academicScore",
        "gradingSystem",
    ]

    for field in required_fields:
        value = getattr(context, field)
        if value is None or (
            isinstance(value, str) and not value.strip()
        ):
            add_error(field, "missing", "필수 입력입니다.")

    has_fields = bool(context.engineeringFields)
    has_interests = any(
        interest.strip() for interest in (context.interests or [])
    )

    if not has_fields and not has_interests:
        add_error(
            "interests",
            "missing",
            "공학 세부 분야 또는 관심 분야를 입력해 주세요.",
        )

    needs_maximum = context.gradingSystem in {"gpa", "total_score"}

    if needs_maximum and context.maximumScore is None:
        add_error(
            "maximumScore",
            "missing_dependency",
            "이 성적 체계에는 만점이 필요합니다.",
        )

    if context.maximumScore is not None:
        if context.maximumScore <= 0:
            add_error(
                "maximumScore",
                "out_of_range",
                "만점은 0보다 커야 합니다.",
            )
        elif (
            context.academicScore is not None
            and context.academicScore > context.maximumScore
        ):
            add_error(
                "academicScore",
                "out_of_range",
                "성적은 만점을 초과할 수 없습니다.",
            )

    if context.academicScore is not None:
        if context.academicScore < 0:
            add_error(
                "academicScore",
                "out_of_range",
                "성적은 음수일 수 없습니다.",
            )
        elif (
            context.gradingSystem == "percentage"
            and context.academicScore > 100
        ):
            add_error(
                "academicScore",
                "out_of_range",
                "백분율 성적은 100을 초과할 수 없습니다.",
            )

    if context.maximumTuition is not None:
        if context.maximumTuition < 0:
            add_error(
                "maximumTuition",
                "out_of_range",
                "최대 학비는 음수일 수 없습니다.",
            )

        if not (context.tuitionCurrency or "").strip():
            add_error(
                "tuitionCurrency",
                "missing_dependency",
                "최대 학비의 통화를 입력해 주세요.",
            )

        if context.tuitionPeriod is None:
            add_error(
                "tuitionPeriod",
                "missing_dependency",
                "최대 학비의 기준 기간을 입력해 주세요.",
            )

    return errors