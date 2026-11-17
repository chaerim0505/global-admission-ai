# 위임 기록 — 성적·학비 맞춤 추천 (F06–F09, AC21–AC28)

- 사용 에이전트: Claude (Cowork) / 위임자: SHWE
- 구현 파일: `src/admission/recommend_v2.py`
- 케이스 파일: `tests/harness/recommend_v2_cases.yaml` (RV-01–RV-17)
- 테스트 코드: `tests/test_recommend_v2_golden.py`
- 결함 주입 스크립트: `scripts/fault_injection.py`

## 1. 작업 지시

- 영어로 질문하면 영어로 응답한다.
- 성적·학비 조건에 맞는 서로 다른 대학 5곳을 추천한다.
- 데이터에 없는 학교·학과는 추천하지 않는다.

## 2. 테스트 하니스

케이스 파일을 읽어 `detect_language()`, `tier_for()`, `recommend()`, `filter_web_results()`, `scholarships_for()`를 호출하고 예상 결과와 비교한다. skip·xfail은 쓰지 않으며, 알 수 없는 expected 키가 있으면 실패한다.

| 실행 (2026-11-18) | 결과 |
| --- | --- |
| `PYTHONPATH=src python -m pytest -q tests/test_recommend_v2_golden.py` | 17 passed, skip·xfail 없음 |
| `python -m pytest -q` (전체, 판정 키 검사 추가 후) | 153 passed, skip·xfail 없음 |
| `python -m pytest -q` (전체, AC20 골든 케이스 추가 후 최신) | 161 passed, skip·xfail 없음 |

## 3. 검토 메모 (위임자)

- F4가 처음에 탐지되지 않음 → 미얀마 국적만 검사하던 빈틈 → 미국 국적 케이스 RV-17 추가.
- F3a는 결과가 원본과 같음 → 예산 초과 과정이 요건 판정에서 다시 제외되는 동등 결함으로 판단 → `budget_fit()` 자체를 바꾸는 F3b 추가.

<!-- fault-injection -->
## 결함 주입 검사 (2026-11-18)

실행: `python scripts/fault_injection.py --write` · 원본 코드는 모든 케이스 통과

| 결함 | 파일 | 바꾼 내용 | 실패한 케이스 |
| --- | --- | --- | --- |
| F1 | src/admission/recommend_v2.py | 상향·안정 판정을 뒤바꿈 (AC25) | RV-09, RV-10 |
| F2 | src/admission/recommend_v2.py | 한 대학 한 과정 규칙 제거 (AC22) | RV-04 |
| F3a | src/admission/recommend_v2.py | recommend()의 예산 초과 제외 줄 제거 (AC24) | 없음 (동등 결함, 3절) |
| F3b | src/admission/recommend_v2.py | budget_fit()이 예산 초과를 within으로 판정 (AC24) | RV-06, RV-07 |
| F4 | src/admission/recommend_v2.py | 국적 목록 밖 장학금도 표시 (AC26) | RV-17 |
| F5 | src/admission/recommend_v2.py | 언어 감지를 무시하고 기본값 사용 (AC21) | RV-02 |
| F6 | src/admission/recommend_v2.py | 웹 결과의 공식 도메인 검사 생략 (AC23) | RV-13 |
