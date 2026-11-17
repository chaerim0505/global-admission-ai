"""Fault injection check for the recommendation golden harness (tests/test_recommend_v2_golden.py).

Each fault copies src/ to a temporary folder, breaks one rule in src/admission/recommend_v2.py,
and runs every case in tests/harness/recommend_v2_cases.yaml against the broken copy.
A good harness must FAIL at least one case for every fault. The result table is written to
docs/prompts/delegation_recommend_v2.md (section "결함 주입 검사").

    python scripts/fault_injection.py            # prints the table
    python scripts/fault_injection.py --write    # also updates the delegation record
"""

from __future__ import annotations

import argparse
import importlib
import shutil
import subprocess
import sys
import tempfile
import types
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = "admission/recommend_v2.py"

# (id, rule broken, AC, old text, new text)
# EQUIVALENT: faults that leave the results unchanged because another rule still enforces the AC.
EQUIVALENT = {
    "F3a": "동등 결함: 예산 초과 과정은 요건 판정(AC6, tuition=unmet)에서 다시 제외되어 결과 목록이 같음 — F3b로 예산 규칙 자체를 검사",
}
FAULTS = [
    ("F1", "상향·안정 판정을 뒤바꿈", "AC25",
     'return "reach"\n    if gap < rules["safety_if_gap_below"]:\n        return "safety"',
     'return "safety"\n    if gap < rules["safety_if_gap_below"]:\n        return "reach"'),
    ("F2", "한 대학 한 과정 규칙 제거(같은 대학 중복 허용)", "AC22",
     "best[uid] = {", 'best[program["programId"]] = {'),
    ("F3a", "recommend()의 예산 초과 제외 줄 제거", "AC24",
     'if fit == "over":', "if False:"),
    ("F3b", "budget_fit()이 예산 초과를 within으로 판정", "AC24",
     'return "within" if cost <= limit else "over"', 'return "within"'),
    ("F4", "국적 목록 밖 장학금도 표시", "AC26",
     "if nationality and listed and nationality not in listed:", "if False:"),
    ("F5", "언어 감지 무시(항상 기본값)", "AC21",
     "if language:\n            return language", "if False:\n            return language"),
    ("F6", "웹 결과의 공식 도메인 검사 생략", "AC23",
     "if status == 200 and _domain_matches(url, domains or []):", "if status == 200:"),
]


def _fake_pytest() -> None:
    """The harness only needs pytest.mark.parametrize at import time; allow running without pytest."""
    if "pytest" in sys.modules:
        return
    try:
        import pytest  # noqa: F401
        return
    except ImportError:
        pass
    fake = types.ModuleType("pytest")
    fake.mark = types.SimpleNamespace(parametrize=lambda *a, **k: (lambda f: f))
    sys.modules["pytest"] = fake


def run_cases(src: Path) -> list[str]:
    """Return the ids of failing cases when the harness runs against `src`."""
    code = f"""
import sys, json, importlib.util, types
sys.path.insert(0, {str(src)!r})
try:
    import pytest
except ImportError:
    fake = types.ModuleType('pytest'); fake.mark = types.SimpleNamespace(parametrize=lambda *a, **k: (lambda f: f))
    sys.modules['pytest'] = fake
spec = importlib.util.spec_from_file_location('h', {str(ROOT / 'tests/test_recommend_v2_golden.py')!r})
h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
failed = []
for case in h.SPEC['cases']:
    try:
        h._run(case)
    except Exception:
        failed.append(case['id'])
print(json.dumps(failed))
"""
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT)
    if out.returncode != 0:
        raise RuntimeError(out.stderr)
    import json
    return json.loads(out.stdout.strip().splitlines()[-1])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    rows = [("원본", "결함 없음", "—", run_cases(ROOT / "src"))]
    for fid, rule, ac, old, new in FAULTS:
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "src"
            shutil.copytree(ROOT / "src", copy, ignore=shutil.ignore_patterns("__pycache__"))
            for shared in ("config", "data"):  # the code reads these relative to the repo root
                (Path(tmp) / shared).symlink_to(ROOT / shared, target_is_directory=True)
            path = copy / TARGET
            text = path.read_text(encoding="utf-8")
            assert text.count(old) == 1, f"{fid}: target text not found once"
            path.write_text(text.replace(old, new), encoding="utf-8")
            rows.append((fid, rule, ac, run_cases(copy)))

    lines = ["| 결함 | 파일 | 바꾼 내용 | 실패한 케이스 |",
             "| --- | --- | --- | --- |"]
    for fid, rule, ac, failed in rows:
        if fid == "원본":
            continue
        result = ", ".join(failed) if failed else ("없음 (동등 결함, 위 검토 메모)" if fid in EQUIVALENT else "없음 (**놓침**)")
        lines.append(f"| {fid} | `{TARGET.replace('admission/', 'src/admission/')}` | {rule} ({ac}) | {result} |")
    table = "\n".join(lines)
    print(table)

    if args.write:
        record = ROOT / "docs/prompts/delegation_recommend_v2.md"
        text = record.read_text(encoding="utf-8")
        marker = "<!-- fault-injection -->"
        head = text.split(marker)[0].rstrip()
        record.write_text(
            f"{head}\n\n{marker}\n## 결함 주입 검사 ({date.today().isoformat()})\n\n"
            "실행: `python scripts/fault_injection.py --write` · 원본 코드는 모든 케이스 통과\n\n"
            f"{table}\n", encoding="utf-8")
    missed = [r[0] for r in rows[1:] if not r[3] and r[0] not in EQUIVALENT]
    return 1 if rows[0][3] or missed else 0


if __name__ == "__main__":
    sys.exit(main())
