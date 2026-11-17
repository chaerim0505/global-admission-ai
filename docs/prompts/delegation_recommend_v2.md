# 위임 기록 — 성적·학비 맞춤 추천 5곳, 웹 보충, 언어, 장학금 (F06–F09, AC21–AC28)

- 위임 대상: 5개국 공식 데이터에서 성적·예산에 맞는 서로 다른 대학 5곳 추천, 부족하면 웹 검색 보충, 질문 언어로 응답, 정부 장학금 안내, 공식 링크 검증
- 에이전트: Claude (Cowork) / 위임자: SHWE (chaerim0505)
- 관련 파일: `src/admission/recommend_v2.py`, `src/admission/requirement_finder.py`, `frontend/app.py`, `config/tiers.yaml`, `config/fx_rates.yaml`, `tests/harness/recommend_v2_cases.yaml`, `tests/test_recommend_v2_golden.py`, `tests/test_requirement_finder.py`, `docs/SPEC.md` F06–F09·AC21–AC28

## 1회차 — 스펙과 골든 케이스 먼저 (2026-11-14)

**프롬프트(원문 요약)**
> 영어로 물어보면 답도 영어로 … 성적이나 학비 조건 있으면 그것과 맞는 대학교 순서로 찾아주고 추천마다 5개 대학 나와야 함 … 실제로 존재하지 않은 학교 학과 추천하지 않아야 해 … 각 나라의 국제 장학금들이 표현해 줘야 해. 교내는 성적에 따라 다를 수 있으니 직접 확인으로.

**결과**
- `docs/SPEC.md`에 F06–F09, AC21–AC27을 먼저 추가하고, `tests/harness/recommend_v2_cases.yaml`(RV-01–RV-14)을 구현 전에 작성했다. 구현 전에는 모든 케이스가 xfail이었다.
- 상향·적정·안정 기준은 사람이 정하도록 `config/tiers.yaml`(±10점, draft)로 분리했다.

## 2회차 — 구현 (2026-11-14)

- `src/admission/recommend_v2.py`: `detect_language`, `tier_for`, `budget_fit`, `recommend`, `filter_web_results`, `scholarships_for`.
- 골든 케이스 RV-01–RV-14 모두 통과 후 xfail 표시를 제거했다(2026-11-18). 지금은 skip·xfail 없이 실패하면 그대로 실패한다.

## 3회차 — 링크 검증과 장학금 확대 (2026-11-14)

**프롬프트(원문)**
> 없는 페이지, 없는 학교, 그리고 그 정보와 상관없는, 관련 없는 링크 주면 안 돼 … 실제로 관련 있는 링크가 돼야 돼

**결과**
- AC28 추가. `src/admission/requirement_finder.py`가 공식 페이지를 직접 열어 값이 본문에 있는지 확인한다. 테스트 13개(`tests/test_requirement_finder.py`).
- 정부 장학금 6 → 11개, 국적 목록 필터(RV-15, RV-16 추가).

**사람의 판단**
- 확인 필요(✅/⚠️) 표시는 빼고, 공식 페이지 링크와 요약만 보여 주기로 결정.
- 교내 장학금은 판정하지 않고 각 대학 공식 페이지로 안내(AC26).

## 4회차 — 결함 주입으로 하니스 점검 (2026-11-18)

- `scripts/fault_injection.py`로 규칙 하나씩 깨뜨려 실행했다(아래 표).
- **첫 실행에서 놓친 결함 2개와 조치**
  - F4(국적 목록 필터 제거): RV-15가 미얀마 국적만 검사해서, 미얀마용 별도 규칙(`myanmarEligible: false`)이 대신 걸러 주는 바람에 놓쳤다 → **RV-17(미국 국적) 추가**, 이제 탐지.
  - F3a(예산 초과 제외 줄 제거): 결과 목록이 원본과 같았다. 예산 초과 과정이 요건 판정(AC6, tuition=`unmet`)에서 다시 제외되기 때문(직접 비교로 확인). 동등 결함으로 기록하고, 예산 규칙 자체를 깨는 **F3b**를 추가해 RV-06·RV-07에서 탐지됨을 확인했다.
- 도구 문제: 처음에는 복사본에 `config/`·`data/`가 없어 모든 결함이 같은 케이스에서 실패하는 거짓 탐지가 나왔다 → 복사본에 두 폴더를 연결하도록 스크립트를 고쳤다.

<!-- fault-injection -->
## 결함 주입 검사 (2026-11-18, `python scripts/fault_injection.py --write`)

각 결함은 `src/` 복사본에서 규칙 하나만 깨뜨린 뒤 `tests/harness/recommend_v2_cases.yaml`의 모든 케이스를 실행한 결과입니다. 원본은 모든 케이스를 통과해야 하고, 각 결함은 하나 이상의 케이스에서 실패해야 합니다.

| 결함 | 바꾼 내용 (`src/admission/recommend_v2.py`) | AC | 실패한 케이스 | 탐지 |
| --- | --- | --- | --- | --- |
| 원본 | 결함 없음 | — | 없음 | — |
| F1 | 상향·안정 판정을 뒤바꿈 | AC25 | RV-09, RV-10 | 탐지 |
| F2 | 한 대학 한 과정 규칙 제거(같은 대학 중복 허용) | AC22 | RV-04 | 탐지 |
| F3a | recommend()의 예산 초과 제외 줄 제거 | AC24 | 없음 | 동등 결함: 예산 초과 과정은 요건 판정(AC6, tuition=unmet)에서 다시 제외되어 결과 목록이 같음 — F3b로 예산 규칙 자체를 검사 |
| F3b | budget_fit()이 예산 초과를 within으로 판정 | AC24 | RV-06, RV-07 | 탐지 |
| F4 | 국적 목록 밖 장학금도 표시 | AC26 | RV-17 | 탐지 |
| F5 | 언어 감지 무시(항상 기본값) | AC21 | RV-02 | 탐지 |
| F6 | 웹 결과의 공식 도메인 검사 생략 | AC23 | RV-13 | 탐지 |
