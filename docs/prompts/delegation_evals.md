# 위임 기록 — Evals 러너와 강의 6 산출물 정리

- 에이전트: Claude (Cowork) / 위임자: SHWE (chaerim0505)
- 날짜: 2026-11-11

## 프롬프트(원문)

> 내 project 이 규칙들에 따라 맞나? (강의 05·06·07 자료, 중간평가 2 안내 첨부)
> B. 기능을 유지하고 스펙을 고치기 … 이 것로 해줘. 남은 것도 다 해야 해

## 에이전트가 만든 것과 사람이 확정할 것

| 산출물 | 강의 기준 작성자 | 이번 상태 |
| --- | --- | --- |
| `docs/ARCHITECTURE.md` | 사람 | 에이전트 **초안**(현재 코드에서 옮겨 적음) — 팀이 검토·확정 |
| `config/rag.yaml` | 사람 | 에이전트 **초안**(현재 구현 값) — 팀이 값과 근거 확정 |
| 도구 표(ARCHITECTURE 3절) | 사람 | 에이전트 초안 — 팀 확정 |
| `src/admission/tools/`, `tests/test_tools.py` | 에이전트(코드) / 사람 검증 | 작성 완료, 결함 주입 확인 |
| `evals/EVAL_DESIGN.md` 지표·목표 | 사람 | 에이전트 초안(AC에서 도출) — 팀 확정 |
| `evals/evalset.jsonl` 25개 | 사람 | 에이전트 초안 — 팀 검토, 50개로 확장 |
| `evals/judge_prompt.md` 루브릭 | 사람 | 에이전트 초안 — 팀 확정 후 라벨로 검증 |
| `evals/judge_labels.jsonl` | **사람만** | 비어 있음 |
| 오류 분석(EVAL_DESIGN 7절) | **사람만**(원문 직접 읽기) | 비어 있음 |
| `evals/run_evals.py` | 에이전트 / 사람 검증 | 작성 완료, 오답 주입 확인 |
| `AGENTS.md` | 사람 | 에이전트 초안 — 팀 확정 |

## 러너 검증

- 실행: `PYTHONPATH=src python evals/run_evals.py` → offline 11/11 통과, live 14개 skip(작업 환경에서 Gemini 접근 불가)
- 오답 주입: `tests/test_run_evals.py` — 데이터에 없는 programId·요청 밖 국가·지시문 값(MIT)·임의 분야·AC19 위반을 넣으면 모두 실패로 판정 (5 passed)
- 도구 계약 결함 주입: 도구를 `write`로 바꾸면 `test_every_tool_is_read_only` 실패, 설명 문장을 바꾸면 `test_tool_set_matches_architecture_table` 실패 → 원복 후 9 passed

## 수용 판단

- [ ] 초안 문서(ARCHITECTURE, rag.yaml, EVAL_DESIGN, AGENTS) 팀 검토
- [ ] `--live --judge --repeat 3` 실행 후 live 베이스라인 기록
- [ ] 수용 / 보류: ____ (팀 작성)
