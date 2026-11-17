# 위임 기록 — Evals 러너 및 검증 도구

- 사용 에이전트: Claude (Cowork) / 위임자: SHWE
- 평가 케이스: `evals/evalset.jsonl`
- 구현 파일: `evals/run_evals.py`, `src/admission/tools/__init__.py`
- 테스트 코드: `tests/test_run_evals.py`, `tests/test_tools.py`

## 1. 작업 지시

- 평가 세트를 읽어 실행·채점하는 러너와, 읽기 전용 도구 및 그 계약 테스트를 만든다.
- 평가 세트·목표·설정값은 사람이 확정한다.

## 2. 결함 주입 검사

| 결함 | 파일 | 바꾼 내용 | 실패한 테스트 |
| --- | --- | --- | --- |
| F1 | src/admission/tools/__init__.py | 도구 하나를 write 도구로 변경 | test_every_tool_is_read_only |
| F2 | src/admission/tools/__init__.py | 도구 설명을 ARCHITECTURE 표와 다르게 변경 | test_tool_set_matches_architecture_table |
| F3 | evals/run_evals.py 채점기 (tests/test_run_evals.py에서 오답 입력) | 없는 programId·요청 밖 국가 / 잘못 채운 항목·주입 지시문 / HTTP 링크·요건 판정 포함 결과를 넣음 | 채점기가 모두 실패 처리함을 확인: test_recommendation_grader_rejects_invented_and_wrong_country, test_intake_grader_rejects_wrong_field_and_injection, test_exploration_grader_rejects_rule_violations |

검사 후 원복, 원복 후 도구 테스트 9 passed.

## 3. 실제 호출 3회 반복 평가 (2026-11-18, judge 없음)

- 실행: `PYTHONPATH=src python evals/run_evals.py --live --repeat 3 --note "midterm2: no judge"`
- 결과 파일: `evals/results/2026-11-18T0456.json`, `evals/results/history.csv`

| 지표 | 결과 | 목표 |
| --- | --- | --- |
| constraint_rate | 18/18 | 100% |
| scope_rate | 6/6 | 100% |
| input_validation_rate | 9/9 | 100% |
| parse_accuracy | 18/18 | 90% |
| injection_resistance | 3/3 | 100% |
| followup_accuracy | 12/12 | 90% |
| explore_rule_compliance | 3/9 (504 시간 초과 6건) | 100%, 미달 |

judge는 평가에서 제외했다(EVAL_DESIGN 6절). 러너의 `--judge` 옵션과 `judge_prompt.md`·`judge_labels.jsonl`은 삭제했다.
