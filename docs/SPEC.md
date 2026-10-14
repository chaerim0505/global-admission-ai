
# Global Admission AI — 제품 스펙 (SPEC)
## 1. 문제
해외 공학 분야 학위 과정에 지원하려는 국제학생은, 여러 페이지에 흩어진 입학 요건·학비·장학금·마감일을 **자기 국적·학력·성적·예산에 맞춰 판단하지 못해**, 학교 하나에 30분–2시간씩 같은 페이지를 반복 확인하고 학교에 이메일로 묻는 데 며칠에서 몇 주를 쓰며, 그래도 자격을 잘못 판단해 장학금 신청이 거절되기도 한다.
## 2. 타깃 사용자
- **1차 사용자:** 지원 국가 5개국의 공학 분야 학부·석사·박사 과정 진학을 희망하는 국제학생.
  - 현재·이전 전공이 공학이 아니어도 대상이다. 실제 전공·선수과목 자격은 과정별 공식 요건으로 판정한다.
  - 국적과 성적표 발급 국가는 제한하지 않는다. 5개국 제한은 **진학 희망 국가**에만 적용한다.

- **비대상(현재):** 공학 외 분야(경영·인문·순수 자연과학·의학 등) 지원자, 5개국 외 국가 진학 희망자, 유학원·입학 담당자, 합격 가능성 예측을 원하는 사용자.
**범위 결정:** 대상 사용자는 해외 진학을 위해 대학·과정·입학 요건 등의 정보를 찾아본 경험이 있는 대학생이며, 서비스 범위를 한국·미국·영국·네덜란드·아일랜드의 5개국과 공학 분야로 한정하는 것은 팀 확정 사항이다. 기존 인터뷰 참여자는 CS 전공 학생이지만, 인터뷰에서 확인한 핵심 문제는 해외 진학 정보의 분산과 지원 자격·학비·장학금 비교의 어려움이다. 데이터 구축과 검증은 공학 분야 내에서 공식 정보를 확보할 수 있는 과정부터 시작하고, 검증이 완료된 과정부터 순차적으로 제공한다.
## 3. 핵심 기능
### 핵심 기능 (한 문장)
사용자의 학력·성적·관심 분야·희망 국가·학비 조건을 입력받아 **지원 국가 5개국에서 공학 분야로 포함 판정을 받은 과정**을 찾고, **입학 요건별 충족 / 미충족 / 확인 필요 판정, 학비·장학금과 각각의 마감일, 추천 이유를 공식 출처·확인일과 함께** 제공한다. 대학원 지원자가 선택하면 지도교수 후보와 관련 논문을 추가한다.
| ID | 기능 | 동작 및 결과 |
| --- | --- | --- |
| F01 | 공학 과정 검색 | 5개국에서 공학 분야 **포함** 판정을 받은 과정 중 국가·학위·세부 분야(`engineeringField`)·관심 분야에 맞는 후보를 검색한다. |
| F02 | 지원 요건 비교 | 공식 학력·전공·선수과목·성적·어학·국적 요건과 사용자 정보를 비교해 항목별로 `충족 / 미충족 / 확인 필요`를 표시한다. |
| F03 | 학비·장학금 안내 | 학비를 예산과 비교하고, 관련 장학금의 금액·자격·신청 마감일·공식 링크를 제공한다. |
| F04 | 과정 추천 | 요건 판정, 세부 분야 적합성, 학비·장학금 조건을 근거로 후보와 추천 이유를 제공한다. |
| F05 | 지도교수 추천 | 석사·박사 지원자가 선택한 경우, **지원 과정과의 연관성이 확인된 교수**의 연구 분야·최근 논문 초록을 관심 분야와 비교해 후보와 관련 논문을 제시한다. |
### 3.1 지원 국가 (5개국)
| 코드 | 국가 | 비고 |
| --- | --- | --- |
| `KR` | 대한민국 | 과정에 따라 어학 요건이 한국어(TOPIK)일 수 있다. |
| `US` | 미국 | |
| `GB` | 영국 | |
| `NL` | 네덜란드 | |
| `IE` | 아일랜드 | |
- 국가 코드는 ISO 3166-1 alpha-2로 저장하며, 검색과 입력 검증에 같은 값을 쓴다.
- 희망 국가를 입력하면 그 국가 안에서만 검색하고, 입력하지 않으면 5개국의 확보된 과정 전체에서 검색한다.
- 5개국 밖의 국가를 요청하면 지원 국가 목록을 안내하며, 다른 국가로 임의 변경하지 않는다.
- 5개국의 모든 공학 과정 제공은 초기 완료 조건이 아니다. 공식 정보를 확보하고 분야 분류를 마친 과정부터 데이터에 넣는다.
### 3.2 공학 분야 포함 기준
과정마다 아래 세부 분야 중 하나를 `engineeringField`로 붙인다.
| `engineeringField` | 해당 전공 예 |
| --- | --- |
| `computing` | Computer Science, Computer Engineering, Software Engineering, AI, Data Science, Cybersecurity |
| `electrical_electronic` | Electrical / Electronic Engineering, Communications |
| `mechanical` | Mechanical Engineering, Robotics, Mechatronics |
| `civil_environmental` | Civil, Structural, Environmental Engineering |
| `chemical_materials` | Chemical Engineering, Materials Science & Engineering |
| `industrial_systems` | Industrial / Systems Engineering, Operations Research |
| `aerospace` | Aerospace / Aeronautical Engineering |
| `biomedical` | Biomedical / Bioengineering |
| `other_engineering` | 위에 없지만 공과대학(Faculty/School of Engineering) 소속 학위 과정 |
- **포함:** 공식 과정 소개·학과 정보·교육과정에서 공학 분야임을 확인할 수 있는 과정. 공과대학 소속이거나 공학 학위(BEng, BS in Engineering, MEng, MSc in Engineering, PhD in Engineering 등)인 과정.
- **명칭만으로 자동 포함하지 않는다.** 과정명이 비슷해도 실제 교육과정이 다를 수 있다(로그 4, 6, 8).
- **융합 과정:** 공식 교육과정의 필수 과목 중 공학 과목 비중을 확인해 팀이 개별 판단한다. 다른 분야 중심의 과정은 제외한다.
- **제외:** 공학 학위가 아닌 과정(MBA, 순수 자연과학, 의학 등).
- **분류 상태:** 과정마다 `included / excluded / needs_review` 중 하나로 기록한다. `needs_review` 과정은 `included`로 확정되기 전까지 추천하지 않는다.
- 과정별로 분류 상태·분류 이유·공식 근거 URL·확인일을 기록한다.
## 4. 범위
### 4.1 포함
- 사용자 입력 → 구조화된 요청(`RequestContext`) 파싱, 필수 입력 누락·성적 범위 오류 시 수정 요청
- 5개국 · 학부/석사/박사 · 공학 분야 포함 판정 과정 검색
- 입학 요건별 `충족 / 미충족 / 확인 필요` 판정과 부족하거나 확인할 조건 안내
- 학비(통화·기간 보존)와 예산 비교, 장학금 자격·금액·마감일 안내
- 입학 마감일과 장학금 마감일의 구분 표시
- 추천 이유, 공학 분야 분류 근거, 항목별 공식 출처 URL·확인일 제공
- 범위 밖 요청(국가·분야)에 대한 지원 범위 안내
- 석사·박사 지원자 선택 시 지도교수 후보·관련 논문 추천
### 4.2 비포함 *(온톨로지 "범위 밖"과 일치시킨다)*
- 5개국 외 국가, 공학 외 분야 과정 추천
- 합격 확률 예측, 종합 점수를 합격 가능성으로 표현하는 것
- 생활비·비자·취업 분석, 대학·전공 순위 산출, 재학생 리뷰 분석
- 지원서 작성·제출, 교수·대학 자동 연락
- 성적표 파일 업로드·자동 추출(확장 기능 — 초기에는 직접 입력만)
- 공식 출처가 없는 정보(커뮤니티 글, 순위 사이트 추정치)를 판정 근거로 쓰는 것
### 4.3 사용자 입력
| 구분 | 입력 항목 | `RequestContext` 필드 |
| --- | --- | --- |
| 필수 | 지원 과정(학부·석사·박사) | `applicantType` |
| 필수 | 현재 또는 최종 학력 | `currentEducationLevel` |
| 필수 | 성적표 발급 국가 | `transcriptCountry` |
| 필수 | 성적, 성적 체계 | `academicScore`, `gradingSystem` |
| 필수 | 공학 세부 분야 또는 관심·연구 분야 | `engineeringFields`, `interests` |
| 조건부 필수 | 만점이 필요한 성적 체계의 최고 점수 | `maximumScore` |
| 조건부 필수 | 최대 학비를 입력했을 때 통화와 기준 기간(학기·연간·전체 과정) | `tuitionCurrency`, `tuitionPeriod` |
| 희망 조건 | 희망 국가, 최대 학비, 장학금 필요 여부, 지도교수 추천 여부 | `preferredCountries`, `maximumTuition`, `scholarshipRequired`, `professorMatchingRequired` |
| 선택 | 국적, 어학 시험 종류·점수 | `nationality`, `languageTestType`, `languageTestScore` |
| 선택 | 출신 학교, 현재·이전 전공, 졸업 여부·예정일, 석차, 활동, 기술, 연구·프로젝트·논문 경험 | 7절 — 온톨로지 반영 후 추가 |
- "필수"는 추천을 실행하기 위한 입력 검증 기준이다. 파서 스키마는 강의 3 규칙(최소 required + null 허용)을 따르고, 누락은 파싱 뒤 검증 단계에서 수정 요청으로 처리한다.
- 공학 세부 분야가 미정이면 "공학 전반"으로 입력할 수 있다(`engineeringFields`를 9개 값 전체로 둔다). 시스템이 특정 세부 분야를 임의로 고르지 않는다.
- 희망 국가가 없으면 5개국 전체에서 검색하고, 최대 학비가 없으면 학비로 제한하지 않는다.
- 지원 과정은 하나의 선택값으로 관리한다 — `RequestContext.applicantType`과 `Program.degreeLevel`은 같은 값 집합이며 같은 학위를 가리킨다.
### 4.4 처리 규칙
**범위와 입력**
- 필수 입력 누락이나 성적 범위 오류(`academicScore > maximumScore` 등)가 있으면 추천을 실행하지 않고 해당 항목의 수정을 요청한다.
- 공학 외 분야나 5개국 밖의 국가를 요청하면 지원 범위를 안내한다. 요청을 임의로 다른 분야·국가로 바꾸지 않는다.
- 공학과 공학 외 분야가 섞여 요청 범위가 모호하면 공학 분야 검색 의도를 확인한다.
- 지도교수 매칭에 정보가 부족하면 연구 관심 분야를 추가로 질문한다.
**지원 요건과 마감일**
- 공식 모집 마감일이 지난 과정은 현재 후보에서 제외한다. 모집 연도·학기·지원자 구분(국제학생 여부)을 함께 확인하며, 마감일이 없거나 적용 시점이 불명확하면 `확인 필요`로 표시한다.
- 필수 입학 요건이 명확히 미충족인 과정은 추천에서 제외하고 사유를 별도 목록으로 안내한다.
- `확인 필요`가 있는 후보를 확정적으로 "지원 가능"이라고 표현하지 않는다.
- 어학 점수 미입력이나 공식 요건 누락은 `미충족`으로 단정하지 않고 `확인 필요`로 둔다. 공식적으로 요구하지 않는 항목은 비교하지 않는다.
- 전공·선수과목·국적 등 자격 판단에 필요한 정보가 없으면 추가 확인 항목으로 안내한다.
- 국가별 성적은 공식 환산·인정 기준이 있을 때만 비교한다. 근거가 없으면 `확인 필요`.
- 공학 외 전공자라는 이유만으로 일괄 제외하지 않는다. 과정별 공식 전공·선수과목 요건으로 판정한다.
**비용과 추천**
- 학비는 같은 통화·기간일 때만 예산과 비교한다. 환산 근거가 없으면 원문 금액·단위를 보여 주고 예산 적합성은 확정하지 않는다.
- 장학금 신청 자격과 실제 수혜 여부를 구분한다. 수혜가 확정되지 않은 장학금을 학비에서 자동으로 빼지 않는다.
- 장학금 공고에 국적 제한이 명시되지 않았으면 "지원 가능"이 아니라 `확인 필요`로 안내한다(로그 10).
- 학부 지원자에게는 지도교수 추천을 적용하지 않는다. 교수의 연구 적합성을 학생 모집 여부로 해석하지 않는다.
- 결과가 없으면 조건을 임의로 완화하지 않고, 제외 사유와 바꿀 수 있는 검색 조건을 안내한다.
- 초기에는 항목별 판정 근거만 제공한다. 종합 적합도 점수는 산식과 가중치를 확정한 뒤 적용하며, 합격 확률로 표현하지 않는다.
- 후보 정렬은 결정론적이어야 한다 — 같은 입력에는 같은 순서. 동점이면 `programId` 오름차순.
## 5. 인터페이스
**`POST /recommend`** — 과정 추천 (F01–F04)
입력 — 파서 출력 `RequestContext` (정본: `src/global_admission/schemas/request_context.schema.json`)
```json
{
  "applicantType": "undergraduate | master | phd | null",
  "engineeringFields": ["computing", "mechanical", "..."],
  "interests": ["string"],
  "preferredCountries": ["KR", "US", "GB", "NL", "IE"],
  "nationality": "MM",
  "currentEducationLevel": "high_school | bachelor | master",
  "transcriptCountry": "MM",
  "academicScore": 3.4,
  "gradingSystem": "gpa | percentage | grade_rank | total_score | other",
  "maximumScore": 4.0,
  "languageTestType": "IELTS | TOEFL_iBT | Duolingo | TOPIK | other",
  "languageTestScore": 6.5,
  "maximumTuition": 20000,
  "tuitionCurrency": "KRW | USD | GBP | EUR",
  "tuitionPeriod": "semester | year | total",
  "scholarshipRequired": true,
  "professorMatchingRequired": false
}
```
출력 (200)
```json
{
  "candidates": [{
    "programId": "string",
    "universityName": "string",
    "country": "KR | US | GB | NL | IE",
    "programName": "string",
    "degreeLevel": "undergraduate | master | phd",
    "engineeringField": "string",
    "fieldClassification": { "status": "included", "reason": "string", "sourceUrl": "string", "checkedAt": "YYYY-MM-DD" },
    "reason": "string",
    "requirements": [{ "item": "string", "status": "met | unmet | needs_check", "evidence": "string", "sourceUrl": "string", "checkedAt": "YYYY-MM-DD" }],
    "tuition": { "amount": 0, "currency": "string", "period": "string", "budgetFit": "within | over | undetermined", "sourceUrl": "string", "checkedAt": "YYYY-MM-DD" },
    "applicationDeadline": { "date": "YYYY-MM-DD | null", "intake": "string", "sourceUrl": "string", "checkedAt": "YYYY-MM-DD" },
    "scholarships": [{ "name": "string", "amount": "string", "eligibility": "string", "nationalityRestriction": "string", "deadline": "YYYY-MM-DD | null", "sourceUrl": "string", "checkedAt": "YYYY-MM-DD" }]
  }],
  "excluded": [{ "programId": "string", "reason": "deadline_passed | requirement_unmet", "detail": "string" }],
  "scopeNotices": ["string"],
  "followUps": ["string"]
}
```
출력 (422) — 필수 입력 누락·범위 오류
```json
{ "inputErrors": [{ "field": "academicScore", "problem": "missing | out_of_range | missing_dependency", "message": "string" }] }
```
**`POST /professors`** — 지도교수 추천 (F05)
- 입력: `{ applicantType, programId, interests[] }`
- 출력: `{ professors: [{ professorName, department, programId, programRelationSource, researchFields[], matchedPapers: [{ title, year, url }], profileUrl, checkedAt }], followUps[] }`
- `applicantType`이 `undergraduate`이면 400과 사유를 반환한다.
- `interests`가 비어 있으면 교수 후보 없이 `followUps`에 연구 관심 분야 질문을 넣는다.
**`GET /health`** — `{ "status": "ok" }`
## 6. 수용 기준 (테스트로 검증 — Definition of Done)
각 AC는 EARS 문형 "[조건]일 때, Global Admission AI는 [동작]한다"로 쓰고, 조건 자리의 유형을 [ ]에 표시한다. AC1–AC11은 10월 7일 판의 번호를 유지하고 AC12부터 원본 명세서에서 되살린 기준을 붙였다.
- **AC1 [상시 적용]:** Global Admission AI는 항상 5개국(`KR`, `US`, `GB`, `NL`, `IE`)의 공학 분야 과정만 후보로 반환한다 — 희망 국가를 입력하지 않은 요청을 포함해, 응답의 `country`가 5개 코드 밖이거나 `engineeringField`가 3.2절 목록 밖이면 실패.
- **AC2 [이벤트 기반]:** 사용자가 `preferredCountries`나 학위를 지정해 추천을 요청하면, Global Admission AI는 해당 국가·학위의 과정만 반환한다 — 지정하지 않은 국가·학위가 결과에 하나라도 있으면 실패.
- **AC3 [상시 적용]:** Global Admission AI는 항상 데이터에 존재하는 대학·과정·장학금·교수만 반환한다 — 모든 `programId`가 데이터에 있어야 하고, 이름을 생성하면 실패.
- **AC4 [상시 적용]:** Global Admission AI는 항상 학비·마감일·장학금·요건 판정·분야 분류마다 공식 출처 URL과 확인일을 포함한다 — 하나라도 `sourceUrl` 또는 `checkedAt`이 비면 실패.
- **AC5 [예외 대응]:** 사용자가 어학 점수·국적·전공 정보를 입력하지 않았거나, 공식 성적 환산 기준이 없거나, 장학금 공고에 국적 제한 여부가 명시되지 않았으면, Global Admission AI는 해당 요건을 `needs_check`로 표시하고 `unmet`으로 단정하지 않으며 확인할 항목을 `followUps`에 넣는다.
- **AC6 [이벤트 기반]:** 공식 마감일이 요청 시점보다 이전인 과정 또는 필수 요건이 명확히 `unmet`인 과정이 있으면, Global Admission AI는 그 과정을 `candidates`에서 빼고 `excluded`에 사유와 함께 넣는다.
- **AC7 [상시 적용]:** Global Admission AI는 항상 학비의 통화·기간을 원문 그대로 보존하고, 입학 마감일(`applicationDeadline`)과 장학금 마감일(`scholarships[].deadline`)을 별도 필드로 반환한다 — 통화나 기간이 다른 학비에 `budgetFit`을 `within` 또는 `over`로 확정하면 실패.
- **AC8 [이벤트 기반]:** 학부 지원자가 지도교수 추천을 요청하면, Global Admission AI는 400과 사유를 반환하고 교수 후보를 내지 않는다.
- **AC9 [예외 대응]:** 조건에 맞는 후보가 없으면, Global Admission AI는 조건을 임의로 완화하지 않고 빈 `candidates`와 함께 제외 사유와 `followUps`를 반환한다.
- **AC10 [예외 대응]:** 수집한 페이지나 논문 초록에 지시문이 들어 있으면, Global Admission AI는 이를 데이터로만 취급하고 판정·순위에 반영하지 않는다(레드티밍 실습에서 검증).
- **AC11 [이벤트 기반]:** `GET /health` 요청이 오면, Global Admission AI는 200과 `{"status":"ok"}`를 반환한다.
- **AC12 [상시 적용]:** Global Admission AI는 항상 분류 상태가 `included`인 과정만 후보로 반환한다 — `fieldClassification.status`가 `excluded`나 `needs_review`인 과정이 `candidates`에 하나라도 있으면 실패.
- **AC13 [예외 대응]:** 사용자가 5개국 밖의 국가나 공학 외 분야를 요청하면, Global Admission AI는 `scopeNotices`에 지원 범위를 안내하고, 요청하지 않은 다른 국가·분야를 대신 검색하지 않는다.
- **AC14 [이벤트 기반]:** 국적이나 성적표 발급 국가가 5개국 밖이거나 현재 전공이 공학이 아닌 사용자가 추천을 요청하면, Global Admission AI는 그것만으로 요청을 거절하거나 과정을 일괄 제외하지 않고 과정별 공식 요건으로 판정한다.
- **AC15 [예외 대응]:** 필수 입력(4.3절)이 없거나 `academicScore`가 `maximumScore`를 넘거나 `maximumTuition`에 통화·기간이 없으면, Global Admission AI는 추천을 실행하지 않고 422와 해당 필드의 `inputErrors`를 반환한다.
- **AC16 [예외 대응]:** 사용자가 공학 세부 분야를 정하지 않았으면, Global Admission AI는 특정 세부 분야를 임의로 고르지 않는다 — 파서 출력의 `engineeringFields`는 null(언급 없음) 또는 9개 값 전체("공학 전반")여야 하며, 발화에 없는 특정 분야(예: "AI니까 `computing`")만 들어 있으면 실패.
- **AC17 [상시 적용]:** Global Admission AI는 항상 수혜가 확정되지 않은 장학금을 학비에서 빼지 않는다 — `tuition.amount`와 `budgetFit`이 장학금 차감 금액으로 계산되어 있으면 실패.
- **AC18 [상시 적용]:** Global Admission AI는 항상 요청한 `programId` 과정과의 관계가 데이터로 확인된 교수만 지도교수 후보로 반환한다 — `programRelationSource`가 비었거나 다른 과정 소속 교수가 있으면 실패.
> 실행 가능한 골든 케이스: `tests/harness/golden_cases.yaml` (케이스마다 `ac:` 필드로 AC 번호를 연결한다). AC11은 구현 상태 확인용, AC10은 레드티밍 케이스로 검증한다.
## 7. 데이터 기준
- 입학·학비·장학금 레코드에는 공식 출처 URL, 확인일, 적용 모집 연도·학기를 기록한다.
- 학비는 금액·통화·기간(학기/연간/전체 과정)을 함께 저장한다. 입학 마감일과 장학금 마감일은 다른 필드다.
- 과정마다 공학 분야 분류 상태(`included / excluded / needs_review`), 분류 이유, 공식 근거 URL, 확인일을 기록한다.
- 교수와 지원 과정의 관계, 소속, 연구 분야의 확인 근거(출처 URL)를 보존한다.
- 누락·상충 정보는 추정해 채우지 않고 비워 둔 뒤 `needs_check`로 처리한다. **데이터 미확보와 실제 조건 미충족을 구분한다.**
- 데이터 모델(클래스·속성·관계)은 `docs/ontology.yaml`을 따른다. 입력 필드는 그 `RequestContext`와 같다.
**구현 전 온톨로지·스키마 반영 필요** (이 스펙이 요구하지만 `ontology.yaml` v2에 아직 없는 것)
- `Program.fieldClassification` — `status`, `reason`, `sourceUrl`, `checkedAt` (3.2절, AC12)
- `Professor` → `Program` 관계와 그 근거 URL (F05, AC18)
- 범위 밖 요청을 파서가 표시할 필드(예: `RequestContext.outOfScopeRequests`)와 `parse_query.md` 반영 (AC13)
- 4.3절 선택 입력(출신 학교, 전공, 졸업 예정일, 석차, 활동, 기술, 연구 경험) — 인터뷰 근거를 붙여 추가할지 결정
## 8. 미확정 사항
- 공학 세부 분야 목록과 융합 과정 포함 기준(3.2절)의 최종 확정
- 국가별 초기 대학·과정 목록과 수량, 데이터 갱신 주기 *(데이터 조사 후)*
- 추천 정렬 방식, 종합 점수를 도입할 경우 산식·가중치 *(추천 설계 시)*
5개국과 공학 분야로 한정한다는 범위 결정은 확정 사항이며, 위 세부 항목과 구분해 관리한다.
