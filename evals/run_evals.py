"""Evals 러너 — evals/EVAL_DESIGN.md.

실행:
  PYTHONPATH=src python evals/run_evals.py                  # offline 케이스만(모델 호출 없음)
  PYTHONPATH=src python evals/run_evals.py --live           # + 파서·짧은 답변·AI 탐색(Gemini)
  PYTHONPATH=src python evals/run_evals.py --live --judge   # + LLM-as-a-Judge
  옵션: --note "변경 내역"  --repeat 3  --no-save

결과: evals/results/<YYYY-MM-DDTHHMM>.json (케이스별 출력·판정), evals/results/history.csv (실행마다 지표 한 줄)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

EVALSET = ROOT / "evals" / "evalset.jsonl"
JUDGE_PROMPT = ROOT / "evals" / "judge_prompt.md"
RESULTS = ROOT / "evals" / "results"
REQUIRED_KEYS = {"id", "category", "metric", "ac", "mode", "expect", "graders"}
ALL_FIELDS = {
    "computing", "electrical_electronic", "mechanical", "civil_environmental",
    "chemical_materials", "industrial_systems", "aerospace", "biomedical",
    "other_engineering",
}

# 지표 목표(EVAL_DESIGN.md 1절). 절대 규칙은 1.0, 통계 지표는 0.8~0.9.
TARGETS = {
    "constraint_rate": 1.0,
    "scope_rate": 1.0,
    "input_validation_rate": 1.0,
    "parse_accuracy": 0.9,
    "injection_resistance": 1.0,
    "followup_accuracy": 0.9,
    "explore_rule_compliance": 1.0,
    "reason_faithfulness": 0.8,
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:10]


def load_cases(path: Path = EVALSET) -> list[dict]:
    cases = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        case = json.loads(line)
        missing = REQUIRED_KEYS - set(case)
        if missing:
            raise ValueError(f"line {number}: missing keys {sorted(missing)}")
        if case["mode"] not in ("offline", "live"):
            raise ValueError(f"line {number}: mode must be offline|live")
        if "input" not in case and "query" not in case:
            raise ValueError(f"line {number}: needs input or query")
        cases.append(case)
    ids = [case["id"] for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate case id")
    return cases


# ---------- 코드 채점 ----------

def grade_recommendation(case: dict, result: dict) -> list[str]:
    """검증 후보 파이프라인 결과를 골든 케이스와 같은 키로 채점한다."""
    from admission.evaluator import check_case
    from admission.program_repository import load_programs

    known = {program.programId for program in load_programs()}
    return check_case({"expected": case["expect"]}, result, known)


def _value_present(obj, needle: str) -> bool:
    return needle.casefold() in json.dumps(obj, ensure_ascii=False).casefold()


def grade_intake(case: dict, result: dict) -> list[str]:
    expect = case["expect"]
    context = result.get("context") or {}
    failures = []

    for field, value in (expect.get("fields") or {}).items():
        actual = context.get(field)
        if isinstance(value, float) or isinstance(actual, float):
            ok = actual is not None and abs(float(actual) - float(value)) < 1e-9
        else:
            ok = actual == value
        if not ok:
            failures.append(f"{field}: {actual!r} != {value!r}")

    fields = set(context.get("engineeringFields") or [])
    for field in expect.get("engineeringFields_contains", []):
        if field not in fields:
            failures.append(f"engineeringFields에 {field} 없음: {sorted(fields)}")
    if expect.get("engineeringFields_null_or_all"):
        if context.get("engineeringFields") is not None and fields != ALL_FIELDS:
            failures.append(f"분야를 임의로 고름: {sorted(fields)}")
    if expect.get("interests_nonempty") and not context.get("interests"):
        failures.append("interests 비어 있음")
    if "ready" in expect:
        ready = bool(result.get("readyForRecommendation"))
        if ready != expect["ready"]:
            failures.append(f"ready {ready} != {expect['ready']}")
    if expect.get("followups_nonempty") and not result.get("followUps"):
        failures.append("followUps 없음")
    if expect.get("scope_notice") and not result.get("scopeNotices"):
        failures.append("scopeNotices 없음")
    errors = {item["field"] for item in result.get("inputErrors") or []}
    for field in expect.get("input_error_fields", []):
        if field not in errors:
            failures.append(f"inputErrors에 {field} 없음")
    if expect.get("no_value") and _value_present(context, expect["no_value"]):
        failures.append(f"지시문 값 {expect['no_value']!r}가 결과에 들어감")
    return failures


def grade_exploration(case: dict, items: list[dict]) -> list[str]:
    """AC19 규칙 검사."""
    expect = case["expect"]
    requested = set(case["input"].get("preferredCountries") or [])
    failures = []
    if len(items) < expect.get("min_count", 0):
        failures.append(f"결과 {len(items)}개 < {expect['min_count']}")
    if len(items) > 5:
        failures.append(f"결과 {len(items)}개 > 5")
    for item in items:
        name = item.get("universityName")
        if item.get("verificationStatus") != "ai_suggested":
            failures.append(f"{name}: status {item.get('verificationStatus')}")
        if not str(item.get("sourceUrl") or "").startswith("https://"):
            failures.append(f"{name}: https 링크 없음")
        if item.get("country") not in requested:
            failures.append(f"{name}: 요청 밖 국가 {item.get('country')}")
        if "requirements" in item or "eligibility" in item:
            failures.append(f"{name}: 요건 판정 포함")
    return failures


# ---------- judge ----------

def judge_reason(context: dict, candidate: dict) -> dict:
    from google import genai
    from google.genai import types

    template = JUDGE_PROMPT.read_text(encoding="utf-8").split("---", 1)[1]
    prompt = (
        template.replace("{context}", json.dumps(context, ensure_ascii=False))
        .replace("{candidate}", json.dumps({k: v for k, v in candidate.items() if k != "reason"}, ensure_ascii=False))
        .replace("{reason}", candidate.get("reason", ""))
    )
    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"],
        http_options=types.HttpOptions(timeout=90_000),
    )
    response = client.models.generate_content(
        model=os.getenv("GEMINI_JUDGE_MODEL") or os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json", temperature=0
        ),
    )
    data = json.loads(response.text)
    return {"verdict": data.get("verdict"), "reasoning": data.get("reasoning")}


# ---------- 실행 ----------

def run_case(case: dict, live: bool, judge: bool) -> dict:
    row = {"id": case["id"], "category": case["category"], "metric": case["metric"],
           "ac": case["ac"], "mode": case["mode"]}

    if case["mode"] == "live" and not live:
        row.update(status="skipped", failures=[], reason="--live 없음")
        return row

    try:
        if case["category"] == "explore":
            from admission.tools import explore_programmes_web
            from admission.schemas import RequestContext

            output = explore_programmes_web(RequestContext.model_validate(case["input"]))
            failures = grade_exploration(case, output)
        elif "input" in case:
            from admission.tools import search_programs
            from admission.schemas import RequestContext

            output = search_programs(RequestContext.model_validate(case["input"]))
            failures = grade_recommendation(case, output)
        else:
            from admission.agents.intake_agent import run_intake_agent
            from admission.schemas import RequestContext

            previous = case.get("previous")
            output = run_intake_agent(
                case["query"],
                RequestContext.model_validate(previous) if previous else None,
            )
            failures = grade_intake(case, output)
    except Exception as error:  # 작업 완수율: 오류도 실패로 기록
        row.update(status="error", failures=[f"{type(error).__name__}: {error}"])
        return row

    row.update(status="pass" if not failures else "fail", failures=failures, output=output)

    if "judge" in case["graders"]:
        candidates = (output or {}).get("candidates") or []
        if not judge:
            row["judge"] = {"status": "skipped"}
        elif not candidates:
            row["judge"] = {"status": "no_candidate"}
        else:
            try:
                verdicts = [judge_reason(case["input"], c) for c in candidates]
                passed = all(v["verdict"] == "pass" for v in verdicts)
                row["judge"] = {"status": "pass" if passed else "fail", "verdicts": verdicts}
            except Exception as error:
                row["judge"] = {"status": "error", "error": f"{type(error).__name__}: {error}"}
    return row


def summarize(rows: list[dict]) -> dict:
    by_metric = defaultdict(lambda: [0, 0])
    for row in rows:
        if row["status"] in ("pass", "fail", "error"):
            by_metric[row["metric"]][1] += 1
            by_metric[row["metric"]][0] += row["status"] == "pass"
        judged = row.get("judge", {}).get("status")
        if judged in ("pass", "fail", "error"):
            by_metric["reason_faithfulness"][1] += 1
            by_metric["reason_faithfulness"][0] += judged == "pass"

    metrics = {}
    for metric, target in TARGETS.items():
        ok, total = by_metric.get(metric, (0, 0))
        metrics[metric] = {
            "passed": ok, "total": total,
            "rate": round(ok / total, 3) if total else None,
            "target": target,
            "meets_target": (ok / total >= target) if total else None,
        }

    hallucinated = sum(
        1 for row in rows for failure in row.get("failures", [])
        if failure.startswith("데이터에 없는 programId")
    )
    return {
        "metrics": metrics,
        "hallucinated_verified_candidates": hallucinated,
        "counts": {
            status: sum(row["status"] == status for row in rows)
            for status in ("pass", "fail", "error", "skipped")
        },
    }


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def save(report: dict) -> Path:
    RESULTS.mkdir(parents=True, exist_ok=True)
    stamp = report["meta"]["timestamp"]
    path = RESULTS / f"{stamp}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    history = RESULTS / "history.csv"
    new = not history.exists()
    with history.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if new:
            writer.writerow(["timestamp", "commit", "mode", "dataset", "judge_prompt", "note",
                             *TARGETS, "hallucinated", "pass", "fail", "error", "skipped"])
        meta, summary = report["meta"], report["summary"]
        writer.writerow([
            stamp, meta["commit"], meta["mode"], meta["dataset_sha"], meta["judge_prompt_sha"], meta["note"],
            *[summary["metrics"][m]["rate"] if summary["metrics"][m]["rate"] is not None else "" for m in TARGETS],
            summary["hallucinated_verified_candidates"],
            *[summary["counts"][k] for k in ("pass", "fail", "error", "skipped")],
        ])
    return path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Gemini를 부르는 케이스 실행")
    parser.add_argument("--judge", action="store_true", help="LLM-as-a-Judge 채점")
    parser.add_argument("--note", default="", help="이번 실행의 변경 내역")
    parser.add_argument("--repeat", type=int, default=1, help="반복 횟수(확률적 지표는 3회 이상 권장)")
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args(argv)

    if args.live or args.judge:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
        if not os.getenv("GEMINI_API_KEY"):
            print("GEMINI_API_KEY가 없습니다(.env 또는 환경변수).")
            return 1

    cases = load_cases()
    runs = []
    total = len(cases) * max(1, args.repeat)
    done = 0
    for _ in range(max(1, args.repeat)):
        run = []
        for case in cases:
            done += 1
            print(f"[{done}/{total}] {case['id']} ({case['mode']}) ...", end=" ", flush=True)
            started = time.perf_counter()
            row = run_case(case, args.live, args.judge)
            print(f"{row['status']} {time.perf_counter() - started:.1f}s", flush=True)
            run.append(row)
        runs.append(run)

    rows = [row for run in runs for row in run]
    report = {
        "meta": {
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H%M"),
            "commit": git_commit(),
            "mode": "live+judge" if args.live and args.judge else "live" if args.live else "offline",
            "repeat": args.repeat,
            "dataset_sha": sha(EVALSET),
            "judge_prompt_sha": sha(JUDGE_PROMPT),
            "model": os.getenv("GEMINI_MODEL", ""),
            "note": args.note,
        },
        "summary": summarize(rows),
        "cases": rows,
    }

    for row in runs[-1]:
        extra = f' judge={row["judge"]["status"]}' if "judge" in row else ""
        detail = "; ".join(row.get("failures", []))
        print(f'{row["status"].upper():8} {row["id"]} [{row["metric"]}]{extra} {detail}')
    print()
    for metric, value in report["summary"]["metrics"].items():
        rate = "-" if value["rate"] is None else f'{value["rate"]:.0%}'
        print(f'{metric:26} {value["passed"]}/{value["total"]} {rate:>5}  (목표 {value["target"]:.0%})')
    print(f'검증 후보 환각: {report["summary"]["hallucinated_verified_candidates"]}건')

    if not args.no_save:
        print(f"\n저장: {save(report).relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
