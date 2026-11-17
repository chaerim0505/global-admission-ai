# Global Admission AI
RAG and Embedding-based AI Agent

# Team Introduction

저희는 소프트웨어학과 23학번 2명으로 구성된 개발팀입니다. 기획, 개발, 테스트와 문서화 업무를 나누고 GitHub Branch와 Pull Request를 활용하여 협업합니다.

## 저장소 구조

백엔드 코드는 `src/admission/` Python 패키지에 있다. 주요 산출물의 위치는 다음과 같다.

| 구분 | 실제 위치 | 내용 |
| --- | --- | --- |
| 스키마 | [`src/admission/schemas/`](src/admission/schemas/) | 추천 요청과 대학 과정 데이터의 JSON 스키마 |
| 프롬프트 | [`src/admission/prompts/`](src/admission/prompts/) | 사용자 발화에서 지원 조건을 추출하는 프롬프트 |
| 도구 | [`src/admission/tools/`](src/admission/tools/) | 과정 검색, 공식 근거 조회, 카탈로그 조회, 웹 탐색 도구 |

## MVP 사용자 가이드

> 2026학년도 2학기 AI 캡스톤디자인 · MVP 사용자 가이드

## 1. 서비스 소개

| | |
| --- | --- |
| 팀 번호 | `Group 7` |
| 팀 이름 | `BridgeU` |
| 서비스 이름 | **Global Admission AI** |
| 대상 사용자 | 한국·미국·영국·네덜란드·아일랜드의 **공학 계열 학부·석사·박사** 진학을 준비하는 유학생 |

**해결하려는 문제** 대학마다 과정 정보와 외국인 모집요강이 흩어져 있어, 내 성적과 예산에 맞는 학교를 고르고 요건을 확인하려면 여러 사이트를 오래 찾아야 합니다. Global Admission AI는 **정부 공개 데이터에 실제로 있는 대학만** 추천하고, 요건은 **대학 공식 페이지에서 확인된 내용만** 보여 줍니다.

**동작 원리: 입력(Input) → 추천(Recommend) → 조사(Research) → 확인(Verify)**

1. **입력** – 학위, 성적, 관심 분야, 희망 국가, 예산을 폼이나 채팅(한국어·영어)으로 입력합니다.
2. **추천** – 5개국 정부 공개 데이터에서 조건에 맞는 **서로 다른 대학 5곳**을 고르고, 상향·적정·안정을 표시합니다.
3. **조사** – 카드 버튼을 누르면 Gemini가 그 대학 공식 사이트에서 학력·어학·학비·장학금·마감일을 찾습니다.
4. **확인** – 링크가 실제로 열리고 그 대학 공식 도메인인 것만 보여 줍니다. 확인되지 않은 내용은 표시하지 않습니다.

**이번 MVP에서 사용할 수 있는 핵심 기능**

- 5개국 **1,542개 대학, 15,896개 공학 과정** 검색 (정부 공개 데이터)
- 성적과 예산에 맞는 **서로 다른 대학 5곳** 추천, **상향(Reach) · 적정(Match) · 안정(Safety)** 표시
- 최대 학비를 넣으면 **예산을 넘는 대학은 제외**
- **🔎 Search official admission requirements**: 공식 사이트 조사, **실제로 열리는 공식 링크만** 표시
- 나라별 **정부 장학금** 안내 (국적이 대상 목록에 없으면 숨김), 교내 장학금은 판정하지 않고 공식 페이지로 안내
- **한국어·영어**: 질문한 언어로 화면과 답변 표시

---

## 2. 실행 및 접속 방법

### 2.1 접속 주소

| 용도 | 주소 |
| --- | --- |
| 서비스 화면 | https://admission-ai-iframfvos6c4n4lnxfvcq3.streamlit.app/ |

### 2.2 지원 환경

- **브라우저:** PC의 최신 Chrome, Edge 또는 Safari. 앱 설치 불필요
- **기기:** PC, 노트북 또는 휴대폰 1대

### 2.3 준비물

- 이메일 주소 (회원가입용, 실제 메일은 보내지 않음)
- 본인 성적(또는 예시 성적)

모든 기능은 운영 서버에서 동작하며, 따로 설치할 것은 없습니다.

---

## 3. 핵심 기능 체험 순서

**가정할 역할:** 미얀마에서 학사를 마치고 해외 공학 석사를 찾는 학생 **체험 목표:** 내 성적과 예산에 맞는 대학 5곳을 받고, 그중 한 곳의 입학 요건을 공식 링크로 확인하기

### 1단계. 계정 만들기 (약 1분)

1. 2.1의 주소를 엽니다. 오른쪽 위 **Language / 언어**에서 한국어 또는 영어를 고릅니다.
2. **Create account**를 고르고 이메일과 비밀번호(8자 이상)를 입력한 뒤 **Create account**를 누릅니다.
3. **Sign in**으로 바꾸고 같은 이메일과 비밀번호로 로그인합니다.

### 2단계. 조건 입력

**① Enter conditions** 탭에서 입력합니다. 예시 조건:

| 입력칸 | 예시 |
| --- | --- |
| Degree | Master |
| Current / highest education | Bachelor |
| Country that issued your transcript | Myanmar (이름을 입력해 고르기) |
| Academic score / Grading system / Maximum score | 3.5 / GPA / 4.5 |
| Engineering fields | Computing (비우면 전체 분야) |
| Preferred countries | South Korea (비우면 전체 5개국) |
| Maximum tuition, currency, period (선택) | 비워 두거나 예산 입력 |
| Nationality (선택) | Myanmar |

**Find sample programmes →** 를 누릅니다. 왼쪽 채팅에 "미얀마에서 학사 졸업했고 GPA 3.5/4.5예요. 한국 컴퓨터 석사 찾아요"처럼 써도 AI가 폼을 채웁니다.

### 3단계. 추천 결과 보기

**② Results** 탭의 **Recommended universities · 5** 아래에 대학 카드 5개가 나옵니다. 카드마다 대학, 과정 · 나라 · 학위, `Reach` / `Match` / `Safety` 배지, 학비, **Official programme page** 링크, 데이터 출처, 난이도 지수가 있습니다.

### 4단계. 공식 입학 요건 확인

카드의 **🔎 Search official admission requirements** 를 누릅니다(10–30초). 학력·어학 요건, 학비, 장학금, 마감일이 정리되고, 내용 옆에 **그 내용이 적힌 공식 페이지 링크**가 붙습니다.

### 5단계. 장학금 확인

결과 아래 **International scholarships**에서 그 나라 정부 장학금의 조건, 혜택, 공식 링크를 봅니다.

### 테스트용 핵심 시나리오 (입력 예 · 기대 결과 · AC)

| # | 범주 | 입력 예 | 기대 결과 | 관련 AC | 자동 검증 |
| --- | --- | --- | --- | --- | --- |
| 1 | 정상 | 한국 · 석사 · 컴퓨팅 · 성적 3.5/4.5 | 서로 다른 대학 5곳, 상향 1 · 적정 3 · 안정 1(가능할 때), 카드마다 출처 표시 | AC22, AC25, AC27 | RV-04, RV-12 |
| 2 | 정상 | 미국 · 학부 · 전기전자 · 최대 학비 35,000 USD/년 | 예산을 넘는 대학 없음, 학비를 모르는 대학은 예산 안 대학 뒤 | AC24 | RV-06, RV-07 |
| 3 | 경계 | 네덜란드 · 석사 · 기계 (조건에 맞는 대학이 5곳 미만) | 있는 만큼(4곳)만 + 부족 이유, 다른 나라·분야를 추가하지 않음 | AC22, AC9 | RV-05 |
| 4 | 경계 | 채팅: "석사 가고 싶어요." | 추천하지 않고 빠진 필수 항목을 물음 | AC15 | GC-02, e07 |
| 5 | 금지 | 채팅: "캐나다 컴퓨터 석사 추천해 주세요." | 지원 범위(5개국) 안내, 다른 나라로 대신 검색하지 않음 | AC13 | GC-03, e05 |
| 6 | 정상 | 영어로 질문: "I want a master's in computing in Korea" | 답변과 화면 문구 모두 영어 | AC21 | RV-01–RV-03 |
| 7 | 금지 | 영국 · 석사 · 국적 미국 | Chevening 표시, GREAT · Commonwealth(국가 목록 밖)는 숨김, 교내 장학금은 판정하지 않음 | AC26 | RV-15, RV-17 |
| 8 | 금지 | 카드에서 🔎 Search official admission requirements | 대학 공식 도메인에서 실제로 열리는 링크만 표시, 비공식·없는 페이지 링크는 제거 | AC28, AC23 | `test_requirement_finder.py`, RV-13 |

---

## 4. 기대 결과 및 확인 방법

### 4.1 결과 화면

| 표시 | 나오는 경우 | 의미 |
| --- | --- | --- |
| `Reach` (상향) | 대학 난이도 지수가 내 성적 점수보다 10점 넘게 높음 | 도전 지원 |
| `Match` (적정) | 차이가 ±10점 이내 | 적정 지원 |
| `Safety` (안정) | 대학 난이도 지수가 10점 넘게 낮음 | 안정 지원 |
| `Within your budget` | 학비가 입력한 최대 학비 이하 | 예산 안 |
| 부족 안내 | 조건에 맞는 대학이 5곳 미만 | 있는 만큼만 보여 주고 이유를 알려 줌 (조건을 임의로 넓히지 않음) |

배지는 공개 지표(미국: 합격률·SAT, 그 외: Leiden Ranking 공학 논문 지표)로 만든 **추정**이며 합격 예측이 아닙니다. 영어 화면에서는 같은 내용이 영어로, 한국어 화면에서는 한국어로 나옵니다.

#### 실제 결과 예시 (2026-11-18, 현재 데이터로 실행한 결과)

**예시 1. 한국 · 석사 · 컴퓨팅 — 성적에 따라 추천이 달라짐**

| 성적 3.5 / 4.5 (점수 77.8) | 배지 | | 성적 4.4 / 4.5 (점수 97.8) | 배지 |
| --- | --- | --- | --- | --- |
| 인하대학교 · 제조AI융합전공 | `Match` | | KAIST · Computing | `Match` |
| 중앙대학교 · AI학과 | `Match` | | 성균관대학교 · Computer Science and Engineering | `Match` |
| 경북대학교 · 모바일통신공학과 | `Match` | | 서울대학교 · Computer Science and Engineering | `Match` |
| 울산과학기술원(UNIST) · 컴퓨터공학과 | `Reach` | | 연세대학교 · 응용인공지능학과 | `Match` |
| 국립부경대학교 · 빅데이터융합학과 | `Safety` | | 영남대학교 · 정보통신공학과 | `Safety` |

**예시 2. 네덜란드 · 석사 · 기계 · 성적 3.5 / 4.0 — 조건에 맞는 대학이 5곳 미만**

| 대학 · 과정 | 배지 |
| --- | --- |
| Delft University of Technology · Mechanical Engineering | `Reach` |
| Eindhoven University of Technology · Automotive Technology | `Match` |
| University of Groningen · Mechanical Engineering | `Match` |
| University of Twente · Mechanical Engineering | `Safety` |

데이터에 조건을 모두 만족하는 대학이 4곳뿐이라 **Recommended universities · 4** 아래에 *"Fewer than five universities meet every condition. Conditions were not relaxed."* 안내가 나옵니다. 앱은 이때 웹 검색으로 같은 조건의 과정을 찾아 보충하며, 공식 링크가 확인되지 않으면 4곳만 보여 줍니다.

### 4.2 결과 확인 방법

- **조건 지키기:** 고른 나라·학위·분야만 나오는지, 같은 대학이 두 번 나오지 않는지 확인합니다.
- **예산:** 최대 학비를 넣으면 그보다 비싼 학비가 카드에 없는지 확인합니다.
- **공식 링크:** 요건 조사 결과의 링크를 눌렀을 때 그 대학 공식 사이트가 열리고, 적힌 점수·금액·날짜가 실제로 있는지 확인합니다.
- **장학금:** 국적을 바꾸면 대상이 아닌 정부 장학금이 사라지는지 확인합니다.

### 4.3 다른 입력으로 다시 실행하기

- **다른 조건:** **① Enter conditions**로 돌아가 조건을 바꾸고 **Find sample programmes →** 를 다시 누릅니다.
- **다른 성적:** 성적을 올리거나 내려서 `Reach` / `Match` / `Safety` 배지가 바뀌는지 봅니다.
- **다른 언어:** 영어로 채팅하면 화면이 영어로 바뀝니다.

---

## 5. 서비스별 추가 안내

### 5.1 계정 / 접근 권한

- 이메일과 비밀번호로 가입·로그인합니다. 이메일 인증은 없습니다.
- 비밀번호는 원문이 아닌 해시(Argon2)로 저장합니다.

### 5.2 사전 준비

- 따로 준비할 것은 없습니다. 본인 성적이 없으면 2단계의 예시 조건을 쓰면 됩니다.

### 5.3 전문 지식 / 특수 환경

- 전문 지식은 필요 없습니다. GPA, 백분율 등 성적 체계와 만점을 함께 넣으면 자동으로 비교합니다.

### 5.4 제한 사항 / 알려진 오류

| 항목 | 내용 / 해결 방법 |
| --- | --- |
| 상향·적정·안정 | 공개 지표로 만든 추정입니다. 실제 합격 결과로 보정하지 않았습니다 |
| 학비 | 미국·한국은 학부 학비만 있습니다. 네덜란드·영국·아일랜드와 대학원 학비는 4단계 공식 요건 조사로 확인하세요 |
| 영국·아일랜드 | 석사 과정만 있습니다 |
| 공식 요건 조사 | Gemini 웹 검색이라 10–30초 걸리고 가끔 시간 초과가 납니다. 잠시 후 다시 누르세요. 확인되지 않은 내용은 표시하지 않습니다 |
| 첫 접속 지연 | 무료 서버가 쉬고 있으면 첫 로그인에 30초–1분이 걸립니다 |
| 범위 밖 기능 | 지도교수 추천(SPEC F05), 5개국 밖 국가, 공학 외 분야 |

---

## 6. 리뷰 기간 운영 (2026년 11월 11일 ~ 18일)

- **11월 11일부터 18일까지** 운영 서버를 사용 가능한 상태로 유지합니다.
- 접속 주소나 실행 방법이 바뀌면 이 가이드를 바로 갱신합니다.
- 문의 및 오류 제보: `syp020320@ajou.ac.kr`, `shwewuttmhone@ajou.ac.kr` (비밀번호는 보내지 마세요)

*최종 수정일:* `2026.11.18`

---

## 7. 개발자 안내: 실행, 테스트, 평가

### 7.1 실행 환경

- Python 3.12, 백엔드 FastAPI(Render), 화면 Streamlit(Streamlit Community Cloud), 계정 DB Neon Postgres(로컬은 SQLite)
- Gemini API 키는 채팅 파싱, 웹 검색 보충, 공식 요건 조사에만 필요합니다. 추천 계산, 골든 테스트, offline evals는 키 없이 실행됩니다.

### 7.2 설치

```bash
git clone https://github.com/chaerim0505/global-admission-ai.git
cd global-admission-ai
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt streamlit openpyxl
```

`requirements.txt`는 백엔드용입니다. 화면 실행에는 `streamlit`, 데이터 생성 스크립트에는 `openpyxl`이 함께 필요합니다(`run_local.sh`와 같은 설치).

### 7.3 환경 변수 (`.env`, 저장소에 올리지 않음)

```bash
GEMINI_API_KEY=발급받은_키
GEMINI_MODEL=gemini-3.8-flash
AUTH_SECRET_KEY=32자_이상의_임의_문자열
```

`DATABASE_URL`이 없으면 `database/users.sqlite`를 사용합니다.

### 7.4 실행

```bash
./scripts/run_local.sh
```

백엔드는 http://127.0.0.1:8001, 화면은 http://localhost:8501 에서 열립니다. 따로 실행하려면:

```bash
PYTHONPATH=src uvicorn admission.main:app --port 8001 --reload
python -m streamlit run frontend/app.py
```

### 7.5 테스트와 평가

```bash
PYTHONPATH=src pytest -q
PYTHONPATH=src python -m admission.evaluator
PYTHONPATH=src python evals/run_evals.py
PYTHONPATH=src python evals/run_evals.py --live --repeat 3 --note "변경 내역"
python scripts/fault_injection.py --write
```

| 명령 | 하는 일 |
| --- | --- |
| `pytest -q` | 골든 케이스(GC·RV·AX)와 단위 테스트 |
| `admission.evaluator` | 골든 케이스 AC별 리포트 |
| `run_evals.py` | evals offline (모델 호출 없음) |
| `run_evals.py --live --repeat 3` | evals live (Gemini 포함), 결과는 `evals/results/` |
| `fault_injection.py --write` | 결함 주입 검사 → `docs/prompts/delegation_recommend_v2.md` |

핵심 테스트 시나리오(입력, 기대 결과, 관련 AC)는 [3절 표](#테스트용-핵심-시나리오-입력-예--기대-결과--ac), 강의 표준 구조와 다른 파일 위치는 [맨 위 표](#평가-항목별-파일-위치-중간평가-2)에 있습니다.

### 7.6 배포

| 대상 | 플랫폼 | 필요한 환경 변수 |
| --- | --- | --- |
| 백엔드 | Render | `GEMINI_API_KEY`, `GEMINI_MODEL`, `AUTH_SECRET_KEY`, `PYTHON_VERSION=3.12.7`, `DATABASE_URL`(Neon) |
| 화면 | Streamlit Community Cloud | Secrets: `API_BASE_URL`, `GEMINI_API_KEY`, `GEMINI_MODEL` |

### 7.7 문서

| 문서 | 내용 |
| --- | --- |
| [`docs/PROBLEM.md`](docs/PROBLEM.md) | 문제 정의 |
| [`docs/SPEC.md`](docs/SPEC.md) | 스펙, 수용 기준(AC1–AC28), **MVP 포함 AC 표는 6.0절** |
| [`docs/ontology.yaml`](docs/ontology.yaml) | 온톨로지 |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | 데이터 흐름, 구성 요소, 도구, RAG, 실패 처리, 가드레일 |
| [`config/rag.yaml`](config/rag.yaml) | RAG 설정 |
| [`AGENTS.md`](AGENTS.md) | 코딩 에이전트 공통 지침 |
| [`tests/harness/`](tests/harness/) | 골든 케이스 |
| [`docs/prompts/`](docs/prompts/) | 위임·검증 기록 |
| [`evals/EVAL_DESIGN.md`](evals/EVAL_DESIGN.md) | 품질 측정 설계, 결과 |
| [`docs/presentations/`](docs/presentations/) | 발표 자료 |

###7.8 평가 항목별 파일 위치 


| 평가 기준 | 안내의 예시 파일 | 저장소 |
| --- | --- | --- |
| 핵심 기능 구현 | `SPEC.md`에 MVP 포함 AC 표시 | [`docs/SPEC.md` 6.0절 "MVP 범위 표시"](docs/SPEC.md) — AC별 MVP 포함 여부와 검증 케이스 표. 구현: [`src/admission/recommend_v2.py`](src/admission/recommend_v2.py), [`src/admission/recommend.py`](src/admission/recommend.py), [`src/admission/requirement_finder.py`](src/admission/requirement_finder.py), [`frontend/app.py`](frontend/app.py) |
| 실행 방법 문서 | README: 실행 환경, 설치·실행 명령, 핵심 시나리오(입력 예·기대 결과·AC) | 이 README의 [2절 실행 및 접속 방법](#2-실행-및-접속-방법), [7절 개발자 안내](#7-개발자-안내-실행-테스트-평가), [3절 「테스트용 핵심 시나리오」](#테스트용-핵심-시나리오-입력-예--기대-결과--ac) |
| 골든 케이스 | `tests/harness/golden_cases.yaml` | 기능별로 4개 파일 — [`golden_cases.yaml`](tests/harness/golden_cases.yaml) (GC, 과정 검색·요건), [`recommend_v2_cases.yaml`](tests/harness/recommend_v2_cases.yaml) (RV, 5곳 추천·예산·등급·언어·장학금), [`ai_exploration_cases.yaml`](tests/harness/ai_exploration_cases.yaml) (AX, 웹 검색 결과), [`intake_followup_cases.yaml`](tests/harness/intake_followup_cases.yaml) (IF, 짧은 답변 해석). 모든 케이스에 `ac`와 `category`(normal 정상 / boundary 경계 / forbidden 금지 행동) |
| 테스트 하니스 | `tests/test_<기능>_golden.py` | [`test_recommend_golden.py`](tests/test_recommend_golden.py) (GC), [`test_recommend_v2_golden.py`](tests/test_recommend_v2_golden.py) (RV), [`test_ai_exploration_golden.py`](tests/test_ai_exploration_golden.py) (AX), [`test_intake_followup_golden.py`](tests/test_intake_followup_golden.py) (IF). skip·xfail 없음 |
| 결함 주입 기록 | `docs/prompts/delegation_<기능>.md` | [`delegation_recommend_v2.md`](docs/prompts/delegation_recommend_v2.md) (맨 아래 결함 주입 표, 도구 [`scripts/fault_injection.py`](scripts/fault_injection.py)), [`delegation_ai_exploration.md`](docs/prompts/delegation_ai_exploration.md), [`delegation_intake_followup.md`](docs/prompts/delegation_intake_followup.md), [`delegation_evals.md`](docs/prompts/delegation_evals.md) |
| evals 설계 | `evals/EVAL_DESIGN.md` | 같음 — [`evals/EVAL_DESIGN.md`](evals/EVAL_DESIGN.md) (지표마다 AC·계산 방법·합격선) |
| evals 데이터셋 | `evals/evalset.jsonl` | 같음 — [`evals/evalset.jsonl`](evals/evalset.jsonl) (25개, 9개 범주) |
| evals 러너 | `evals/run_evals.py` | 같음 — [`evals/run_evals.py`](evals/run_evals.py) |
| evals 결과·이력 | `evals/results/`, `evals/results/history.csv` | 같음 — [`evals/results/`](evals/results/), [`history.csv`](evals/results/history.csv) |
| judge 사람 라벨 | `evals/judge_labels.jsonl` (judge 사용 시) | 현재 judge를 쓰지 않음 — 이유는 [`evals/EVAL_DESIGN.md` 6절](evals/EVAL_DESIGN.md) |
| CI | — | [`.github/workflows/tests.yml`](.github/workflows/tests.yml) — push마다 pytest, 골든 리포트, offline evals |
