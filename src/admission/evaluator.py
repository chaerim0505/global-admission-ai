"""골든 케이스로 /recommend 파이프라인을 평가한다.

실행: PYTHONPATH=src python -m admission.evaluator [cases.yaml]
"""

import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import yaml

from admission.program_repository import load_programs
from admission.program_schemas import Program
from admission.recommend import recommend
from admission.schemas import RequestContext


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES = PROJECT_ROOT / "tests" / "harness" / "golden_cases.yaml"


def _all_sourced(candidate: dict) -> bool:
    items = [candidate["fieldClassification"], *candidate["requirements"]]
    items += candidate["scholarships"]
    if candidate["tuition"] is not None:
        items.append(candidate["tuition"])
    return all(item.get("sourceUrl") and item.get("checkedAt") for item in items)


def check_case(
    case: dict,
    result: dict,
    known_ids: set[str] | None = None,
) -> list[str]:
    """실패 사유 목록을 반환한다. 비어 있으면 통과."""
    expected = case.get("expected", {})
    failures = []
    status = 422 if "inputErrors" in result else 200

    if expected.get("status", 200) != status:
        return [f"status {status} != {expected.get('status', 200)}"]

    if status == 422:
        fields = {e["field"] for e in result["inputErrors"]}
        for field in expected.get("input_error_fields", []):
            if field not in fields:
                failures.append(f"inputErrors에 {field} 없음")
        return failures

    candidates = result["candidates"]
    ids = {c["programId"] for c in candidates}
    excluded_ids = {e["programId"] for e in result["excluded"]}

    if "countries_only" in expected:
        allowed = set(expected["countries_only"])
        bad = [c["programId"] for c in candidates if c["country"] not in allowed]
        if bad:
            failures.append(f"허용 밖 국가: {bad}")

    if "degree_only" in expected:
        bad = [
            c["programId"]
            for c in candidates
            if c["degreeLevel"] != expected["degree_only"]
        ]
        if bad:
            failures.append(f"허용 밖 학위: {bad}")

    for program_id in expected.get("must_include", []):
        if program_id not in ids:
            failures.append(f"{program_id} 누락")

    for program_id in expected.get("must_exclude", []):
        if program_id in ids:
            failures.append(f"{program_id}가 후보에 있음")

    for program_id in expected.get("excluded_include", []):
        if program_id not in excluded_ids:
            failures.append(f"{program_id}가 excluded에 없음")

    if expected.get("candidates_empty") and candidates:
        failures.append("후보가 비어 있어야 함")

    if expected.get("must_have_source"):
        bad = [c["programId"] for c in candidates if not _all_sourced(c)]
        if bad:
            failures.append(f"출처 누락: {bad}")

    if expected.get("scope_notice") and not result["scopeNotices"]:
        failures.append("scopeNotices 없음")

    for item in expected.get("needs_check_items", []):
        found = any(
            r["item"] == item and r["status"] == "needs_check"
            for c in candidates
            for r in c["requirements"]
        )
        if not found:
            failures.append(f"{item}이 needs_check가 아님")

    if "budget_fit" in expected:
        for c in candidates:
            fit = (c["tuition"] or {}).get("budgetFit")
            if fit is not None and fit != expected["budget_fit"]:
                failures.append(f'{c["programId"]} budgetFit {fit}')

    if expected.get("follow_ups_nonempty") and not result["followUps"]:
        failures.append("followUps 없음")

    if expected.get("ids_in_data") and known_ids is not None:
        bad = sorted(ids - known_ids)
        if bad:
            failures.append(f"데이터에 없는 programId: {bad}")

    if expected.get("budget_fit_undecided"):
        for c in candidates:
            fit = (c["tuition"] or {}).get("budgetFit")
            if fit in ("within", "over"):
                failures.append(f'{c["programId"]} budgetFit 확정됨: {fit}')

    return failures


def run(
    cases: list[dict],
    programs: list[Program] | None = None,
    today: date | None = None,
) -> dict:
    programs = load_programs() if programs is None else programs
    by_ac = defaultdict(lambda: [0, 0])
    rows = []
    hallucinations = 0

    for case in cases:
        context = RequestContext.model_validate(case.get("input", {}))
        result = recommend(context, programs=programs, today=today)
        failures = check_case(
            case, result, {program.programId for program in programs}
        )
        hallucinations += len(result.get("validationIssues", []))

        for ac in case.get("ac", []):
            by_ac[ac][1] += 1
            if not failures:
                by_ac[ac][0] += 1

        rows.append({"id": case["id"], "passed": not failures, "failures": failures})

    passed = sum(row["passed"] for row in rows)

    return {
        "total": len(rows),
        "passed": passed,
        "passRate": round(passed / len(rows), 3) if rows else 0.0,
        "validationIssues": hallucinations,
        "byAc": {ac: f"{ok}/{n}" for ac, (ok, n) in sorted(by_ac.items())},
        "cases": rows,
    }


def load_cases(path: Path = DEFAULT_CASES) -> list[dict]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or []


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CASES
    report = run(load_cases(path))

    for row in report["cases"]:
        mark = "PASS" if row["passed"] else "FAIL"
        print(f'{mark} {row["id"]} {"; ".join(row["failures"])}')

    print(
        f'\n통과 {report["passed"]}/{report["total"]} '
        f'({report["passRate"]:.0%}), 검증 이슈 {report["validationIssues"]}건'
    )
    print(json.dumps(report["byAc"], ensure_ascii=False))
