# 위임 기록 — AI 탐색 결과(검증 전) (F06, AC19)

- 사용 에이전트: Claude (Cowork) / 위임자: SHWE
- 구현 파일: `src/admission/ai_exploration.py`, `frontend/app.py`
- 케이스 파일: `tests/harness/ai_exploration_cases.yaml` (AX-01–AX-06)
- 테스트 코드: `tests/test_ai_exploration_golden.py`

## 1. 작업 지시

- 검증 데이터에 맞는 과정이 없으면 Gemini 웹 검색으로 추가 과정을 찾아 자동으로 보여 준다.
- 스펙 충돌(AC3 "데이터에 있는 과정만 반환"): 사람이 기능 유지를 선택 → AC3를 검증 후보로 한정하고 AC19 추가, 검증 후보와 AI 탐색 결과를 분리.

## 2. 테스트 하니스

케이스 파일을 읽어 `parse_json_list()`, `normalize_items()`를 호출하고 예상 결과와 비교한다. skip·xfail은 쓰지 않는다.

| 실행 (2026-11-18) | 결과 |
| --- | --- |
| `PYTHONPATH=src python -m pytest -q tests/test_ai_exploration_golden.py` | 8 passed, skip 없음 |

## 3. 결함 주입 검사

| 결함 | 파일 | 바꾼 내용 | 실패한 케이스 |
| --- | --- | --- | --- |
| F1 | src/admission/ai_exploration.py | HTTPS 링크 검사 제거 | AX-02 |
| F2 | src/admission/ai_exploration.py | 요청 국가 검사 제거 | AX-03 |
| F3 | src/admission/ai_exploration.py | 검증 후보 대학 제외 규칙 제거 | AX-04 |

검사 후 원복, 원복 후 8 passed.

## 4. 실제 Gemini 호출 (evals/results/2026-11-18T0228.json)

- e23–e25 각 3회: 4/9 통과 (목표 100%, 미달)
- 오류 5건(e24 2건, e25 3건)은 모두 `504 DEADLINE_EXCEEDED`(Gemini 응답 시간 초과)
