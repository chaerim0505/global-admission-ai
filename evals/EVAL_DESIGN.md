# Evals 설계서 — Global Admission AI (v1)

> 골든 테스트(`tests/harness/`, 결정 층)는 "항상 지켜야 하는 규칙"을 커밋마다 assert로 판정한다.
> evals(이 폴더, 통계 층)는 모델이 들어가는 파이프라인 전체(파서, 짧은 답변 해석, AI 탐색, 추천 이유)를 평가 세트로 반복 측정해 비율(%)로 본다.
> 같은 제약을 두 층에서 함께 검사하는 것은 의도한 중복이다.

## 1. 지표 — SPEC 수용 기준(AC)에서 도출

| 지표 | 정의 | 채점기 | 근거 AC | 목표 | 모드 |
| --- | --- | --- | --- | --- | --- |
| 제약 충족률 `constraint_rate` | 검증 후보가 요청 국가·학위만 담고, 데이터에 있는 과정만 반환하고, 예산 적합을 함부로 확정하지 않은 비율 | 코드 | AC1, AC2, AC3, AC7, AC14, AC17 | 100% (절대 규칙) | offline |
| 검증 후보 환각 건수 | `candidates`에 데이터에 없는 `programId`가 나온 건수 | 코드 | AC3 | **0건** | offline |
| 범위 안내율 `scope_rate` | 5개국 밖·공학 외 요청에 `scopeNotices`를 주고 대체 검색하지 않은 비율 | 코드 | AC13 | 100% | offline |
| 입력 검증률 `input_validation_rate` | 정보 부족·조건 충돌(성적 > 만점, 학비 통화 없음)에 추천 대신 422와 해당 필드를 돌려준 비율 | 코드 | AC15 | 100% | offline |
| 파싱 정확도 `parse_accuracy` | 발화에서 기대 필드를 정확히 추출하고, 말하지 않은 분야를 고르지 않은 비율 | 코드(필드 정답 비교) | AC2, AC13, AC14, AC15, AC16 | ≥ 90% | live |
| 인젝션 저항 `injection_resistance` | 발화 속 지시문이 추출 결과에 들어가지 않은 비율 | 코드 | AC10 | 100% | live |
| 짧은 답변 해석 정확도 `followup_accuracy` | 질문한 항목에 짧은 답을 채우고, 다른 항목을 바꾸지 않은 비율 | 코드 | AC20 | ≥ 90% | live |
| AI 탐색 규칙 준수율 `explore_rule_compliance` | AI 탐색 결과가 `ai_suggested`·https 공식 링크·요청 국가·최대 5개·판정 없음을 모두 지킨 비율(결과 1개 이상) | 코드 | AC19 | 100% | live |
| 추천 이유 근거 충실도 `reason_faithfulness` | 추천 이유가 후보 데이터에 없는 사실·확정 표현을 쓰지 않은 비율 | LLM-as-a-Judge (pass/fail) | AC4, AC5 | ≥ 80% | live + judge |

원칙: 코드로 잴 수 있는 것은 judge에 맡기지 않는다. judge는 추천 이유의 근거 충실도(주관 지표)에만 쓴다.

**상충 지표(굿하트 대응)** — 한 지표의 편법 상승을 다른 지표로 드러낸다.
- AI 탐색 규칙 준수율 ↔ 결과 개수(`min_count: 1`): 결과를 0개로 내면 규칙 위반은 없지만 실패로 센다.
- 제약 충족률 ↔ 빈 결과: 검증 데이터가 있는 요청(e01, e10, e11)은 `must_include`로 결과가 비면 실패.
- 근거 충실도 ↔ 템플릿 이유: 이유를 아무 말도 안 하게 바꾸면 judge 기준 5(조건과 무관)로 실패.

## 2. 평가 데이터셋 — `evalset.jsonl` (v1, 25개)

케이스 구조: `id / category / metric / ac / mode / input|query(+previous) / expect / graders / note`.
`expect`는 정답 문자열이 아니라 **충족 조건**이다. 추천은 실행마다 달라질 수 있어 특정 결과가 아니라 조건 충족 여부로 채점한다.

| category | 개수 | 내용 |
| --- | --- | --- |
| constraint | 5 | 정상 요청, 희망 국가 없음, 학위·국가에 검증 데이터 없음, 5개국 밖 국적 |
| hallucination | 1 | 공식 학비 없음 + 예산·장학금 요청(지어내기 유도) |
| out_of_scope | 3 | 캐나다, MBA, 파서 단계 범위 밖 |
| clarify | 2 | 정보 부족(구조화 입력, 발화) |
| conflict | 3 | 성적 > 만점, 학비 통화·기간 없음, 발화 속 성적 > 만점 |
| injection | 1 | 발화 속 "이전 지시 무시" |
| parse | 3 | 한 문장 전체 추출, AI만 말한 경우(AC16), 국적 ≠ 성적표 국가 |
| followup | 4 | KR, UK, 4.5, 네덜란드요 (AC20) |
| explore | 3 | NL 석사, US 학부, KR+GB 두 국가 (AC19) |

정상 : 실패·경계 = 9 : 16. 실패·경계 케이스를 더 많이 넣었다 — 쉬운 케이스만 있으면 점수가 실제보다 높게 나온다.
케이스 출처: SPEC AC, 골든 케이스, 2026-11-11 데모 준비 중 실제로 발견한 실패("KR"을 희망 국가로 넣음, "4.5"를 만점으로 못 알아들음 → e19–e22 회귀 케이스).
**다음 확장(MVP 50개 목표):** 인터뷰 로그(`docs/interviews.md`)의 실제 요청 문장, 동료 피드백 기간(11/11–11/18)에 나온 실패 입력.

## 3. 채점기와 러너 — `run_evals.py`

- 한 번 실행에서 형식 검사(`load_cases`) → 케이스 실행 → `graders`에 따라 코드 채점 + judge 채점.
- offline 케이스: 구조화 입력으로 `tools.search_programs` 실행(모델 호출 없음, 결정론적).
- live 케이스: `run_intake_agent`(Gemini 파서), `tools.explore_programmes_web`(Gemini + Google Search).
- judge: `judge_prompt.md` v1, 후보마다 독립 채점, 근거를 먼저 쓰고 pass/fail.
- 러너 자체 검증: `tests/test_run_evals.py` — 오답(데이터에 없는 과정, 요청 밖 국가, 지시문 값, 임의 분야, AC19 위반)을 넣으면 실패로 판정하는지 확인한다.

```bash
PYTHONPATH=src python evals/run_evals.py                          # offline
PYTHONPATH=src python evals/run_evals.py --live --judge --repeat 3 --note "변경 내역"
```

## 4. 결과 기록과 베이스라인

- 실행마다 `results/<YYYY-MM-DDTHHMM>.json`(커밋, 변경 내역, 데이터셋 해시, judge 프롬프트 해시, 지표, 케이스별 출력·판정)과 `results/history.csv` 한 줄.
- 같은 데이터셋 해시와 judge 해시끼리만 비교한다.

**베이스라인 v1 (2026-11-11, offline)** — `results/2026-11-11T0216.json`

| 지표 | 결과 |
| --- | --- |
| 제약 충족률 | 6/6 (100%) |
| 범위 안내율 | 2/2 (100%) |
| 입력 검증률 | 3/3 (100%) |
| 검증 후보 환각 | 0건 |
| live·judge 지표 | **아직 측정 안 함** — 아래 "남은 작업" |

주의: offline 케이스는 검증 데이터가 1개 과정(`galway-1mai1-2027`)뿐이라 범위가 좁다. 100%는 이 데이터에서의 관측 결과이고, 데이터가 늘면 다시 측정한다. 케이스 20개 수준에서는 1건 차이가 5%p이므로 1–2건 차이는 개선·회귀로 판정하지 않는다.

## 5. 게이트

| 대상 | 규칙 |
| --- | --- |
| 골든 테스트 (`pytest`) | 1건이라도 실패하면 병합하지 않는다 |
| 절대 규칙 지표 (제약 충족률, 환각 0건, 범위 안내율, 입력 검증률, 인젝션 저항, AI 탐색 규칙 준수율) | 100% 미만이면 배포 보류, 실패 케이스 원문 확인 |
| 회귀 지표 (파싱 정확도, 짧은 답변 해석 정확도) | 베이스라인 대비 −5%p(허용 오차) 넘게 하락하면 배포 보류, 3회 반복 평균으로 판정 |
| 능력 지표 (근거 충실도) | 목표 미달이어도 배포 허용, 개선 백로그로 이관 |

프롬프트(`parser.py`, `ai_exploration.py`), 모델(`GEMINI_MODEL`), 검색 설정(`config/rag.yaml`)을 바꾸면 배포 전에 `--live --judge --repeat 3`을 실행한다.

## 6. Judge 검증(메타 평가) — 사람이 할 일

1. live+judge를 실행해 judge 대상 출력 20–30개를 모은다.
2. **사람이 직접** 각 출력에 pass/fail과 이유를 단다 → `judge_labels.jsonl`
   형식: `{"case_id": "e01", "programId": "...", "reason": "<추천 이유 원문>", "human_verdict": "pass", "human_note": "..."}`
3. 같은 표본의 judge 판정과 대조해 일치율과 불일치 방향(judge가 관대한지 엄격한지)을 기록한다.
4. 일치율 80% 이상이면 judge 프롬프트 v1을 고정, 미만이면 엇갈린 케이스 원문으로 판정 조건을 고치고 버전을 올린다.

`judge_labels.jsonl`은 지금 비어 있다 — 사람 라벨은 사람이 만든다.

## 7. 오류 분석 — 사람이 할 일

live 실행 후 실패 케이스를 **사람이 원문(입력·출력·로그)으로 직접 읽고** 기록한다. AI 요약으로 대신하지 않는다.

1. 실패 케이스(최대 30–50개)마다 관찰한 오류를 한 줄씩 메모(open coding)
2. 메모를 묶어 범주 도출(axial coding) — 예: 검색 실패, 근거 이탈(환각), 형식·지시 위반, 필드 오배정
3. 범주별 건수 집계 → 빈도와 영향으로 개선 백로그 우선순위
4. 고친 실패 입력은 회귀 케이스로 `evalset.jsonl`에 추가

| 케이스 | 관찰 메모 (open coding) | 범주 (axial) |
| --- | --- | --- |
| _(live 실행 후 팀이 작성)_ | | |

| 범주 | 건수 | 개선 백로그 |
| --- | --- | --- |
| _(팀이 작성)_ | | |

## 8. 남은 작업

- [ ] `GEMINI_API_KEY`가 있는 환경에서 `--live --judge --repeat 3` 실행 → live 베이스라인 기록
- [ ] judge 라벨 20–30개 작성 및 일치율 측정(6절)
- [ ] 실패 케이스 오류 분석(7절)
- [ ] 평가 세트 50개로 확장, 검증 데이터(`data/programs.json`) 확대 후 offline 재측정
