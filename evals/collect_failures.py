"""evals 결과에서 실패·오류 케이스를 모아 오류 분석용 표를 만든다.

실행: python evals/collect_failures.py            # 모든 결과 파일
      python evals/collect_failures.py <결과.json>  # 특정 실행만
출력: evals/ERROR_ANALYSIS.md 의 "원문" 표를 다시 쓴다.

이 스크립트는 원문(입력, 실패 내용)만 모은다. 메모·범주는 사람이 원문을 읽고 직접 쓴다
(강의 7: 실패 케이스 검토를 AI 요약으로 대체하지 않음). 이미 쓴 메모는 지우지 않는다.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "evals" / "results"
EVALSET = ROOT / "evals" / "evalset.jsonl"
OUT = ROOT / "evals" / "ERROR_ANALYSIS.md"
START = "<!-- failures:start -->"
END = "<!-- failures:end -->"


def load_inputs() -> dict:
    cases = {}
    for line in EVALSET.read_text(encoding="utf-8").splitlines():
        if line.strip():
            case = json.loads(line)
            cases[case["id"]] = case.get("query") or json.dumps(case.get("input"), ensure_ascii=False)
    return cases


def cell(text: str, limit: int = 160) -> str:
    text = " ".join(str(text).split()).replace("|", "/")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def main(argv: list[str]) -> int:
    files = [Path(a) for a in argv] or sorted(RESULTS.glob("*.json"))
    inputs = load_inputs()
    rows = []
    for path in files:
        report = json.loads(path.read_text(encoding="utf-8"))
        run = path.stem
        for case in report.get("cases", []):
            judge = case.get("judge", {}).get("status")
            if case["status"] in ("fail", "error") or judge in ("fail", "error"):
                problem = "; ".join(case.get("failures", [])) or f"judge {judge}"
                rows.append(f"| {run} | {case['id']} | {case['metric']} | {cell(inputs.get(case['id'], ''))} | {cell(problem)} |")

    table = "\n".join([
        START,
        f"실패·오류 {len(rows)}건 (자동 수집, 원문)",
        "",
        "| 실행 | 케이스 | 지표 | 입력 | 실패 내용 |",
        "| --- | --- | --- | --- | --- |",
        *(rows or ["| - | - | - | - | 실패 없음 |"]),
        END,
    ])

    text = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
    if START in text and END in text:
        text = text[: text.index(START)] + table + text[text.index(END) + len(END):]
    else:
        text = table + "\n" + text
    OUT.write_text(text, encoding="utf-8")
    print(f"{len(rows)}건 → {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
