# 공식 페이지에서 사람이 확인해 입력한 실험용 기준
# https://gradadmissions.stanford.edu/apply/test-scores
minimum_ielts = 7.0

# 가상 사용자: 시험 유효기간은 충족한다고 가정
user_ielts = None
english_test_exempt = True  # 영어 시험 면제 대상 여부

print("비교 대상: Stanford 대학원 공통 IELTS 기준")
print(f"기준 점수: {minimum_ielts}")
print(f"사용자 점수: {user_ielts}")

if english_test_exempt:
    print("결과: 영어 시험 면제 대상으로 가정하여 점수 비교 생략")
elif user_ielts is None:
    print("결과: 확인 필요 — 영어 점수 정보 없음")
elif user_ielts >= minimum_ielts:
    print("결과: 대학원 공통 최소 영어 점수 충족")
else:
    print("결과: 대학원 공통 최소 영어 점수 미충족")

print("학과별 추가 조건과 다른 지원 요건은 별도 확인이 필요합니다.")