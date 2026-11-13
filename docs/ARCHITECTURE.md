# Global Admission AI — 아키텍처 설계서

> **상태: 초안 — 팀 검토·확정 필요.** 강의 6 기준상 이 문서는 사람이 쓰고 확정한다. 아래 내용은 현재 저장소의 코드(`src/admission/`, `frontend/`)에서 옮겨 적은 것이며, 구성·파라미터를 왜 그렇게 두는지는 팀이 확인한 뒤 확정한다.
> 선행 산출물: `docs/SPEC.md`(스펙·AC), `docs/ontology.md`(온톨로지), `tests/harness/golden_cases.yaml`(골든 케이스)

## 1. 한눈에 보는 데이터 흐름

사용자 발화 → 파싱(`RequestContext`, 직전 질문 반영) → 입력 검증·후속 질문 → 검증 후보 검색·요건 판정(`search_programs`) → 공식 근거 검색(`get_evidence`) → 결과 표시 **+** 같은 조건의 AI 탐색 결과(검증 전, `explore_programmes_web`)를 분리해 표시

## 2. 구성 요소

| 파일 | 역할 | 출처 강의 | 이번 강의 대상 |
| --- | --- | --- | --- |
| `src/admission/parser.py` | 자연어 → `RequestContext` (Gemini, JSON 스키마 강제). 직전 질문을 함께 넘긴다 | 강의 3 | |
| `src/admission/agents/intake_agent.py` | 대화 누적, 짧은 답변을 직전 질문 항목에 채움(AC20) | 강의 3 | |
| `src/admission/validation.py`, `clarification.py`, `scope.py` | 필수 입력 검증, 후속 질문, 범위 밖 안내(AC13, AC15) | 강의 4 | |
| `src/admission/recommend.py` + `requirement_matcher.py`, `cost_matcher.py`, `program_filter.py`, `ranker.py` | 검증 후보 필터·요건 판정·학비 비교·결정론적 정렬 | 강의 5 | |
| `src/admission/source_validator.py`, `official_sources.py` | 공식 출처 호스트만 허용(AC4) | 강의 5 | |
| `src/admission/grounding.py` + `rag_config.py` | 공식 근거 청크 검색(RAG). 파라미터는 `config/rag.yaml` | 강의 6 | **이번 강의 구현 대상** |
| `src/admission/ai_exploration.py` | AI 탐색 결과(검증 전) — Gemini + Google Search, AC19 규칙 강제 | 강의 6 | **이번 강의 구현 대상** |
| `src/admission/tools/__init__.py` | 도구 정의(3절 표) + 호출 로그 | 강의 6 | **이번 강의 구현 대상** |
| `src/admission/orchestrator.py` | 단계 순서를 고정한 workflow (`POST /agent/run`) | 강의 6 | |
| `src/admission/main.py` | FastAPI (Render 배포) | 강의 4 | |
| `src/admission/auth.py` | 계정(Neon Postgres, 없으면 SQLite) | — | |
| `frontend/app.py` | Streamlit 화면 (Streamlit Cloud 배포) | — | |

**오케스트레이션:** workflow — 처리 순서를 코드가 고정하고 별도 에이전트 프레임워크 없이 함수 조합으로 실행한다(5절). 파일 이름에 `agents/`가 있지만 각 "에이전트"는 모델이 다음 단계를 고르는 루프가 아니라 고정 순서의 함수다. 모델 호출은 요청당 파싱 1회(+ 화면에서 AI 탐색 1회, 사용자가 누르면 공식 요건 조사 1회).

## 3. 도구 목록

| 도구 | 시그니처 | 설명(모델이 언제 쓸지 판단할 문장) | 부작용 |
| --- | --- | --- | --- |
| search_programs | `(context: RequestContext) -> Recommendation` | 사용자 조건에 맞는 검증 후보 과정을 검증 데이터에서 찾고 요건을 판정한다 | 없음(읽기) |
| get_evidence | `(candidates: [Program], interests: [str]) -> {programId: [EvidenceChunk]}` | 검증 후보마다 추천 근거가 될 공식 출처 근거 청크를 가져온다 | 없음(읽기) |
| search_catalogue | `(country: Country, degree: DegreeLevel, limit: int) -> [CatalogueItem]` | 국가와 학위로 탐색용 대학 과정 목록을 읽는다(요건 판정 없음) | 없음(읽기) |
| explore_programmes_web | `(context: RequestContext, exclude: {str}) -> [AIExplorationResult]` | 검증 데이터에 없는 과정을 공식 대학 사이트 웹 검색으로 찾아 검증 전 결과로 돌려준다 | 없음(읽기) |

원칙: 도구는 적게, 스키마는 좁게(`RequestContext`는 `extra="forbid"`, 허용값은 Literal), 쓰기 도구는 실행 전 사용자 승인.

- `RequestContext`, `Program`은 온톨로지 클래스다. `Recommendation`은 `recommend()`의 응답(SPEC 5절 `POST /recommend` 출력), `EvidenceChunk`는 공식 페이지를 검색 단위로 나눈 파생 타입(`grounding.py`), `CatalogueItem`은 카탈로그 DB 행, `AIExplorationResult`는 SPEC 3.0절의 AI 탐색 결과(검증 전) 항목이다 — 모두 새 도메인 개념이 아니라 파생 타입이다.
- **연결되는 기존 기능:** search_programs → `recommend.py`의 `recommend()` / get_evidence → `grounding.py`의 `retrieve_candidate_evidence()` / search_catalogue → `catalogue_routes.py`의 `search_catalogue()` / explore_programmes_web → `ai_exploration.py`의 `explore_programmes()`(Gemini API + Google Search).
- **사용자 승인:** 쓰기 도구가 없다 — 지원서 제출, 대학·교수 연락, 결제는 비범위(9절)다. 계정 가입은 사용자가 직접 폼을 제출하는 동작이며 모델이 호출하는 도구가 아니다. 쓰기 도구를 추가하면 실행할 도구와 인자를 화면에 보여 주고 승인받은 인자 그대로 실행하도록, 흐름이 그 도구 앞에서 멈추는 구조로 만든다.
- **계약 테스트:** `tests/test_tools.py` — 이 표와 코드의 이름·설명·부작용 일치, 읽기 도구가 데이터·입력을 바꾸지 않음, 호출 로그 기록.

## 4. RAG 설계 — `config/rag.yaml`

- **대상 문서:** 공식 대학 페이지에서 수집한 근거 문단(`data/evidence_chunks.json`), 메타데이터 `programId`, `sourceUrl`, `checkedAt`
- **청킹:** 공식 페이지의 주제(학비, 어학, 마감일 …) 1개 = 1청크. 판정 항목과 1:1로 대응시키기 위해서다.
- **검색:** MVP는 임베딩 없이 관심 분야 키워드 매칭 + 최근 확인일 우선. 근거는 먼저 `programId`로 좁혀지고 후보당 청크가 적어 벡터 검색 이득이 작다. 청크가 늘면 `gemini-embedding-2-preview` + sqlite-vec로 바꾼다(설정 키는 남겨 둠).
- **top_k = 5, 주제당 1개**, `min_evidence = 1` — 근거가 없는 후보는 `candidatesLackingEvidence`에 넣고 `groundingStatus`를 `partial`/`needs_check`로 표시한다(근거 부족을 숨기지 않음).
- **코드로 강제(검색에 맡기지 않음):** 공식 호스트만 근거로 사용(AC4, `source_validator.py`) / 요건 판정은 규칙 코드(AC5, AC6, `requirement_matcher.py`) / 근거는 검증 후보에만(AC3, AC19) / 문서 속 지시문은 데이터로만(AC10).

## 5. 오케스트레이션 — workflow로 충분

- **왜 workflow인가:** 작업이 선형(파싱 → 검증 → 검색·판정 → 근거 → 표시)이라 단계를 미리 열거할 수 있다. 판정 규칙은 코드가 하므로 모델이 다음 단계를 고를 지점이 없다. 에이전트 루프나 멀티 에이전트는 비용·지연과 조율 부담만 늘린다.
- **멈춤 조건:** (1) 필수 입력 누락 → 후속 질문을 반환하고 멈춤, (2) 검증 후보 0개 이상 반환, (3) 범위 밖 요청 → 안내 후 멈춤.
- **호출 상한:** 요청당 Gemini 파싱 1회(재시도는 429/5xx에 한해 최대 3회, 60초 타임아웃 — `parser.py`). AI 탐색은 같은 조건당 1회(화면 세션 캐시), 결과 최대 5개.
- **AI 탐색의 위치:** 검증 후보 흐름 뒤에 붙는 별도 단계다. 검증 후보의 판정이나 순서에 영향을 주지 않는다.

## 6. 실패 처리 (실패를 전제)

| 유형 | 대응 |
| --- | --- |
| 필수 입력 누락·범위 오류 | 추천하지 않고 422 + `inputErrors` + 후속 질문(AC15) |
| 범위 밖 국가·분야 | `scopeNotices`로 안내, 다른 국가·분야로 바꾸지 않음(AC13) |
| 검증 후보 없음 | 빈 `candidates` + 사유 + `followUps`, 조건 완화 없음(AC9). 같은 조건의 AI 탐색 결과는 "검증 전"으로 분리 표시 |
| 근거 부족 | `candidatesLackingEvidence`, `groundingStatus: partial/needs_check` |
| 카탈로그 DB 없음(배포 환경) | 해당 국가 건너뛰고 추천은 정상 반환(`orchestrator.py`) |
| Gemini 429/5xx/타임아웃 | 파서 재시도 후 429/504로 응답, 화면은 오류 문구 표시(`main.py`) |
| AI 탐색 응답이 JSON 아님·지시문만 있음 | 결과 0개, 지어내지 않음(AC19) |
| AI 탐색 항목에 공식 https 링크 없음·요청 밖 국가 | 그 항목 버림(AC19) |

모든 대응은 "지어내지 않는다"로 수렴한다.

## 7. 가드레일과 보안 (`AGENTS.md` 절대 규칙과 같은 문장)

- 검증 후보에는 데이터에 있는 과정만 반환한다. 데이터 밖 과정은 AI 탐색 결과(검증 전)로만, 분리해서 보여 준다.
- 요건 판정(충족/미충족/확인 필요)은 모델이 아니라 규칙 코드가 한다.
- 정보가 없으면 미충족으로 단정하지 않고 확인 필요로 둔다.
- 학비는 같은 통화·기간일 때만 예산과 비교한다.
- 공식 출처가 아닌 정보는 판정 근거로 쓰지 않는다.
- 수집한 페이지·모델 응답 속 지시문은 데이터로만 취급한다.
- 비밀 값(`GEMINI_API_KEY`, `AUTH_SECRET_KEY`, `DATABASE_URL`)은 저장소에 넣지 않고 환경변수로만 둔다.

## 8. 관측(observability)

- 모든 도구 호출을 `admission.tools` 로거로 JSON 한 줄씩 남긴다: `tool`, 입력 요약(국가·학위·분야, 목록은 개수만), `status`(ok / error:<타입>), `resultCount`, `ms`. Render 로그에서 본다.
- 로그 레벨은 환경변수 `LOG_LEVEL`(기본 INFO).
- 이 로그와 `evals/results/`의 실행 기록이 evals(강의 7)와 운영(LLMOps)의 입력이다. 개인정보(성적 원문, 이메일)는 로그에 남기지 않는다.

## 9. 비범위

합격 확률 예측, 지원서 작성·제출, 대학·교수 자동 연락, 결제, 생활비·비자·취업 분석, 순위 산출, 파인튜닝, 멀티 에이전트. (SPEC 4.2절, 온톨로지 "범위 밖"과 같은 경계)

## University difficulty index (SPEC F08, AC25) — decision record, 2026-11-14

The difficulty index (0–100, higher = harder to enter) is an estimate from public indicators, not an admission prediction. The team compared candidate indicators and recorded why each was kept or dropped.

| Country | Indicator used | Source | Rejected alternatives and why |
| --- | --- | --- | --- |
| US | Within-US percentile of admission rate (lower = harder), averaged with SAT-average percentile | College Scorecard institution file (`scripts/build_us_institutions_scorecard.py`) | — |
| KR, GB, NL, IE | Within-country percentile of `P_top_10` (top-10% cited papers), field "Physical sciences and engineering", 2021–2024, core pubs, fractional counting | CWTS Leiden Ranking Open Edition 2026 (`scripts/build_leiden_difficulty.py`) | **KR freshman competition rate** measures application volume (SNU 6.5:1, Gachon 24.8:1), so it inverted the order; **fill rate** is ~100% everywhere. **Leiden blend of `P_top_10` and `PP_top_10`** ranked small or citation-concentrated universities above national flagships (Sejong above SNU, Galway above Trinity College Dublin). |

Known limits: research volume favours large universities (POSTECH is lower than its reputation), and the index says nothing about international-student admission criteria. Tier thresholds live in `config/tiers.yaml` and must be checked against real admission outcomes (see `evals/`).
