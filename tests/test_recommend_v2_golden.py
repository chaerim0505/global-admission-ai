"""Golden cases for SPEC F06-F09 / AC21-AC27, written before implementation.

Each case is xfail until src/admission/recommend_v2.py provides:
  detect_language(messages) -> "en" | "ko"
  tier_for(applicant, university_index, rules) -> "reach" | "match" | "safety" | "unknown"
  recommend(context, catalogue, rates_to_usd, web_results=None) -> {"results": [...], "shortfallReason": str | None}
  filter_web_results(items) -> list
  scholarships_for(context) -> {"national": [...], "university": {...}}
"""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = yaml.safe_load((ROOT / "tests/harness/recommend_v2_cases.yaml").read_text(encoding="utf-8"))
RULES = yaml.safe_load((ROOT / "config/tiers.yaml").read_text(encoding="utf-8"))

try:
    from admission import recommend_v2 as rv
except ImportError:  # not implemented yet (test first)
    rv = None


def _run(case):
    fx = SPEC["fixtures"]
    kind, exp = case["kind"], case["expected"]
    if kind == "language":
        assert rv.detect_language(case["messages"]) == exp["language"]
    elif kind == "tier":
        assert rv.tier_for(case["applicant"], case["university_index"], RULES) == exp["tier"]
    elif kind == "web_check":
        kept = rv.filter_web_results(case["web_results"])
        assert [k["universityName"] for k in kept] == exp["kept"]
        assert all(k["source"] == exp["all_source"] for k in kept)
    elif kind == "scholarships":
        out = rv.scholarships_for(case["context"])
        ids = {s["scholarshipId"] for s in out["national"]}
        assert set(exp["includes_national"]) <= ids
        assert out["university"]["status"] == exp["university_status"]
    elif kind == "recommend":
        out = rv.recommend(case["context"], fx["catalogue"], fx["rates_to_usd"], case.get("web_results"))
        res = out["results"]
        names = [r["universityName"] for r in res]
        if "count" in exp:
            assert len(res) == exp["count"]
        if exp.get("distinct_universities"):
            assert len(set(names)) == len(names)
        if exp.get("all_have_source"):
            assert all(r.get("source") for r in res)
        if exp.get("has_shortfall_reason"):
            assert out["shortfallReason"]
        if "countries_only" in exp:
            assert {r["country"] for r in res} <= set(exp["countries_only"])
        for absent in exp.get("absent_universities", []):
            assert absent not in names
        if exp.get("unknown_tuition_after_known"):
            fits = [r["budgetFit"] for r in res]
            if "needs_check" in fits:
                assert "within" not in fits[fits.index("needs_check"):]
        if "tier_counts" in exp:
            counts = {}
            for r in res:
                counts[r["admissionTier"]] = counts.get(r["admissionTier"], 0) + 1
            assert counts == exp["tier_counts"]
    else:
        raise AssertionError(f"unknown kind {kind}")


@pytest.mark.parametrize("case", SPEC["cases"], ids=[c["id"] for c in SPEC["cases"]])
def test_recommend_v2_golden(case):
    needed = {"language": "detect_language", "tier": "tier_for", "web_check": "filter_web_results",
              "scholarships": "scholarships_for", "recommend": "recommend"}[case["kind"]]
    if rv is None or not hasattr(rv, needed):
        pytest.xfail(f"{needed} not implemented yet (golden cases written first)")
    _run(case)
