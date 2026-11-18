"""채팅 요약이 결과 탭과 같은 추천 결과를 말하는지 검사한다 (D2, AC9, AC21).

추천 결과는 recommend_v2 골든 케이스의 고정 데이터(RV-04, RV-05)로 만든다. 결과 탭은 같은
recommend() 결과로 카드를 그리므로, 채팅 요약에 나온 대학 수와 이름이 결과와 같아야 한다.
"""

from pathlib import Path

import pytest
import yaml

from admission import recommend_v2 as rv
from admission.chat_summary import (
    build_summary,
    merge_previous_context,
    unsupported_countries,
    unsupported_message,
)

ROOT = Path(__file__).resolve().parents[1]
SPEC = yaml.safe_load((ROOT / "tests/harness/recommend_v2_cases.yaml").read_text(encoding="utf-8"))
CASES = {case["id"]: case for case in SPEC["cases"]}


def _outcome(case_id):
    case = CASES[case_id]
    fx = SPEC["fixtures"]
    return rv.recommend(case["context"], fx["catalogue"], fx["rates_to_usd"], case.get("web_results"))


@pytest.mark.parametrize("case_id", ["RV-04", "RV-05"])
@pytest.mark.parametrize("lang", ["en", "ko"])
def test_summary_lists_exactly_the_results_tab_universities(case_id, lang):
    outcome = _outcome(case_id)
    text = build_summary(outcome["results"], bool(outcome["shortfallReason"]), lang)

    numbered = [line for line in text.splitlines() if line[:2].rstrip(".").isdigit()]
    assert len(numbered) == len(outcome["results"])
    for line, item in zip(numbered, outcome["results"]):
        assert item["universityName"] in line
    assert str(len(outcome["results"])) in text.splitlines()[0]


def test_shortfall_is_stated_and_never_relaxed():
    outcome = _outcome("RV-05")  # only 2 KR civil programmes
    assert outcome["shortfallReason"]
    en = build_summary(outcome["results"], True, "en")
    ko = build_summary(outcome["results"], True, "ko")
    assert "Conditions were not relaxed." in en
    assert "조건은 완화하지 않았습니다." in ko


def test_summary_follows_screen_language():
    results = [{"universityName": "Trinity College Dublin", "programName": "Biomedical Engineering (M.Sc.)",
                "admissionTier": "unknown", "source": "web_verified"}]
    en = build_summary(results, True, "en")
    ko = build_summary(results, True, "ko")
    assert "Found by web search" in en and "웹 검색" not in en
    assert "웹 검색으로 찾음" in ko and "Found by web search" not in ko
    assert "not yet verified" in en


def test_no_results_message_in_each_language():
    assert "No universities matched every condition" in build_summary([], False, "en")
    assert "조건은 완화하지 않았습니다" in build_summary([], False, "ko")


def test_web_search_notice_is_passed_through():
    notice = "Web search is taking too long right now. Please try again in a moment."
    assert notice in build_summary([], True, "en", web_notice=notice)


def test_unsupported_countries_are_reported():
    assert unsupported_countries(["IE", "de", "DE", "KR"]) == ["DE"]
    assert "Germany is not supported yet" in unsupported_message(["Germany"], "en")
    assert "아직 지원하지 않아요" in unsupported_message(["독일"], "ko")


def test_form_values_fill_the_chat_context_without_blanks():
    merged = merge_previous_context(
        {"applicantType": "master", "academicScore": 3.0},
        {"academicScore": 4.0, "maximumScore": 4.5, "nationality": None, "engineeringFields": []},
    )
    assert merged == {"applicantType": "master", "academicScore": 4.0, "maximumScore": 4.5}
