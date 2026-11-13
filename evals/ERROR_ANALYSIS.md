# 오류 분석 — evals v1

> 절차 (강의 7, EVAL_DESIGN.md 7절): 원문 읽기 → 메모(open coding) → 범주(axial coding) → 빈도 → 개선 백로그 → 고친 입력은 회귀 케이스로 evalset에 추가.
> **아래 "원문" 표는 `python evals/collect_failures.py`가 결과 파일에서 자동으로 모은 것이다. 메모·범주·백로그는 사람이 원문(`evals/results/<실행>.json`의 해당 케이스 output)을 직접 읽고 쓴다. AI 요약으로 대신하지 않는다.**
> 표본이 적으면(현재 1건) 판단하지 않고, `--live --repeat 3` 실행과 케이스 확장으로 실패 표본을 30–50건까지 모은 뒤 범주화한다.

## 1. 원문 (자동 수집)

<!-- failures:start -->
실패·오류 1건 (자동 수집, 원문)

| 실행 | 케이스 | 지표 | 입력 | 실패 내용 |
| --- | --- | --- | --- | --- |
| 2026-11-11T0246 | e23 | explore_rule_compliance | {"applicantType": "master", "currentEducationLevel": "bachelor", "transcriptCountry": "MM", "academicScore": 3.4, "gradingSystem": "gpa", "maximumScore": 4.0, … | ServerError: 504 DEADLINE_EXCEEDED. {'error': {'code': 504, 'message': 'Deadline expired before operation could complete.', 'status': 'DEADLINE_EXCEEDED'}} |
<!-- failures:end -->

## 2. 메모 (open coding) — 사람이 작성

| 실행 | 케이스 | 원문을 읽고 관찰한 것 (한 줄) | 작성자 |
| --- | --- | --- | --- |
| | | | |

## 3. 범주와 빈도 (axial coding) — 사람이 작성

| 범주 | 건수 | 해당 케이스 |
| --- | --- | --- |
| | | |

## 4. 개선 백로그 — 사람이 작성

| 우선순위 | 범주 | 할 일 | 회귀 케이스 추가 |
| --- | --- | --- | --- |
| | | | |
