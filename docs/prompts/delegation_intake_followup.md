# 위임 기록 — 짧은 답변 해석 (AC20)

- 위임 대상: 채팅에서 시스템이 질문한 뒤 사용자가 짧게 답하면 그 항목에 채우기
- 에이전트: Claude (Cowork) / 위임자: SHWE (chaerim0505)
- 관련 파일: `src/admission/parser.py`, `src/admission/agents/intake_agent.py`, `tests/test_intake_pending_answer.py`

## 1회차 — 국가 답변 (2026-11-11)

**프롬프트(원문)**
> KR 든 korea 든 안되고 왜 반복?
> kr 써든 뭐 써든 잘 이해해야 하지 않아?얘가 묻는 질문 답한 건데
> 한국뿐만 아니라 모든 후보 국가 5개가 그레야 해

**원인 분석(에이전트)** — `parse_query`가 "KR" 한 단어만 받아 직전 질문을 몰랐다. 모델이 KR을 `preferredCountries`에 넣어 `transcriptCountry`가 계속 비어 같은 질문이 반복됐다(화면에서 Preferred countries = South Korea, Transcript country = 빈칸으로 확인).

**결과**
- 파서에 직전 질문을 함께 전달(`[직전 질문]` + `[사용자 답변]`) — 모든 항목에 적용.
- 안전장치: 성적표 국가 질문에 국가 이름만 답하면 `transcriptCountry`에 채우고, 모델이 같은 값을 희망 국가에 넣었으면 되돌림. 5개국 + MM의 코드·영문·한글·말끝("요", "입니다") 처리.
- 실행: `pytest -q tests/test_intake_pending_answer.py` → 통과(국가 표현 5개국 케이스 포함)
- 커밋: `943eb59 Treat short answers as replies to the pending question` (사람이 push)

## 2회차 — 숫자 답변 (2026-11-11)

**프롬프트(원문)**
> 그리고 성직 발급 국가나 제일 많은 것 얼마냐 물어보면 4.5 라고 하면 왜 gpa maximum인 것 몰라

**결과**
- 숫자만 답하면(“4.5”, “4.5점”, “만점은 4.5점이요”) 열린 숫자 질문이 하나일 때 그 항목(성적/만점/최대 학비)에 채움. 모델이 질문하지 않은 숫자 항목에 넣었으면 되돌림. 숫자 질문이 여러 개면 모델 판단에 맡김.
- 실행: 관련 테스트 36개 통과(작업 환경, `google-genai`는 스텁)
- 커밋: `7f4f75d Fill numeric answers into the field that was asked` (사람이 push)

## 남은 확인

- 실제 Gemini로의 확인은 evals `e19–e22`(`--live`)로 측정한다.
- [ ] 수용 / 보류: ____ (팀 작성)
