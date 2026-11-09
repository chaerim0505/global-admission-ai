QUESTIONS = {
    "applicantType": "학부·석사·박사 중 어떤 과정에 지원하시나요?",
    "currentEducationLevel": "현재 또는 최종 학력이 무엇인가요?",
    "transcriptCountry": "성적표를 발급한 국가는 어디인가요?",
    "academicScore": "현재 또는 최종 학교 성적은 얼마인가요?",
    "gradingSystem": "성적 체계는 GPA·백분율·등급·총점 중 무엇인가요?",
    "maximumScore": "입력한 성적의 만점은 얼마인가요?",
    "interests": "희망하는 공학 세부 분야나 관심·연구 분야는 무엇인가요?",
    "engineeringFields": "희망하는 공학 세부 분야는 무엇인가요?",
    "tuitionCurrency": "최대 학비의 통화는 무엇인가요? 예: EUR, USD, KRW",
    "tuitionPeriod": "최대 학비는 학기·연간·전체 과정 중 어떤 기준인가요?",
    "maximumTuition": "부담 가능한 최대 학비는 얼마인가요?",
}


def build_follow_ups(
    input_errors: list[dict[str, str]],
) -> list[dict[str, str]]:
    follow_ups = []
    seen = set()

    for error in input_errors:
        field = error["field"]

        if field in seen:
            continue

        seen.add(field)

        if error["problem"] == "out_of_range":
            question = (
                f'{error["message"]} 해당 값을 확인하고 다시 입력해 주세요.'
            )
        else:
            question = QUESTIONS.get(
                field,
                f'{error["message"]} 해당 항목을 확인해 주세요.',
            )

        follow_ups.append({
            "field": field,
            "question": question,
        })

    return follow_ups