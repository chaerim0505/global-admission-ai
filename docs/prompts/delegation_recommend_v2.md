# 위임 기록 — 성적·학비 맞춤 추천 (F06–F09, AC21–AC28)

- 위임자: SHWE (chaerim0505) / 에이전트: Claude (Cowork)
- 하니스: `tests/harness/recommend_v2_cases.yaml` → `tests/test_recommend_v2_golden.py`

## 검토 메모 (위임자)

- F4가 처음에 탐지되지 않음 → 미얀마 국적만 검사하던 빈틈을 확인하고 RV-17(미국 국적) 추가를 결정.
- F3a는 결과가 원본과 같음 → 예산 초과 과정이 요건 판정(AC6)에서 다시 제외되는 동등 결함으로 판단, 예산 판정 자체를 깨는 F3b를 추가.

<!-- fault-injection -->
## 결함 주입 검사 (2026-11-18)

실행: `python scripts/fault_injection.py --write` · 원본 코드는 모든 케이스 통과

| 결함 | 파일 | 바꾼 내용 | 실패한 케이스 |
| --- | --- | --- | --- |
| F1 | `src/admission/recommend_v2.py` | 상향·안정 판정을 뒤바꿈 (AC25) | RV-09, RV-10 |
| F2 | `src/admission/recommend_v2.py` | 한 대학 한 과정 규칙 제거(같은 대학 중복 허용) (AC22) | RV-04 |
| F3a | `src/admission/recommend_v2.py` | recommend()의 예산 초과 제외 줄 제거 (AC24) | 없음 (동등 결함, 위 검토 메모) |
| F3b | `src/admission/recommend_v2.py` | budget_fit()이 예산 초과를 within으로 판정 (AC24) | RV-06, RV-07 |
| F4 | `src/admission/recommend_v2.py` | 국적 목록 밖 장학금도 표시 (AC26) | RV-17 |
| F5 | `src/admission/recommend_v2.py` | 언어 감지 무시(항상 기본값) (AC21) | RV-02 |
| F6 | `src/admission/recommend_v2.py` | 웹 결과의 공식 도메인 검사 생략 (AC23) | RV-13 |
