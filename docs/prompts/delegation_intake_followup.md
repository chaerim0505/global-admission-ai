# 위임 기록 — 짧은 답변 해석 (AC20)

- 사용 에이전트: Claude (Cowork) / 위임자: SHWE
- 구현 파일: `src/admission/agents/intake_agent.py`, `src/admission/parser.py`
- 케이스 파일: `tests/harness/intake_followup_cases.yaml` (IF-01–IF-07)
- 테스트 코드: `tests/test_intake_followup_golden.py`, `tests/test_intake_pending_answer.py`

## 1. 작업 지시

- 성적표 발급 국가 질문에 KR, Korea, 한국처럼 짧게 답하면 성적표 발급 국가로 인식하고 같은 질문을 반복하지 않는다. (커밋 943eb59)
- 만점을 묻는 질문에 4.5처럼 숫자만 답하면 질문한 항목(성적·만점·최대 학비)에 채운다. (커밋 7f4f75d)

## 2. 테스트 하니스

케이스 파일을 읽어 `run_intake_agent()`를 호출하고 예상 결과와 비교한다. 모델 응답은 케이스의 `model_output`으로 고정한다. skip·xfail은 쓰지 않으며, 알 수 없는 expected 키가 있으면 실패한다.

| 실행 (2026-11-18) | 결과 |
| --- | --- |
| `PYTHONPATH=src python -m pytest -q tests/test_intake_followup_golden.py` | 8 passed (케이스 7개 + 형식 검사), skip 없음 |
| `PYTHONPATH=src python -m pytest -q tests/test_intake_pending_answer.py` | 8 passed, skip 없음 |

## 3. 결함 주입 검사 (2026-11-18)

| 결함 | 파일 | 바꾼 내용 | 실패한 케이스 |
| --- | --- | --- | --- |
| F1 | src/admission/agents/intake_agent.py | 국가 답변 보정(`_apply_country`) 호출 제거 | IF-01, IF-02 |
| F2 | src/admission/agents/intake_agent.py | 숫자 답변 보정(`_apply_number`) 호출 제거 | IF-04, IF-05, IF-06 |
| F3 | src/admission/agents/intake_agent.py | 희망 국가에 잘못 들어간 답변을 지우는 줄 제거 | IF-02 |

검사 후 원복, 원복 후 8 passed.

## 4. 실제 모델 호출 (evals/results/2026-11-18T0456.json)

- e19–e22 각 3회: followup_accuracy 12/12
