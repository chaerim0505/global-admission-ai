"""Data checks for data/catalogue/programs_unified.json (SPEC 3.0, 3.1, 3.2, AC1, AC23, AC27)."""

import json
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "data" / "catalogue" / "programs_unified.json"
FIELDS = {"computing", "electrical_electronic", "mechanical", "civil_environmental", "chemical_materials",
          "industrial_systems", "aerospace", "biomedical", "other_engineering"}

pytestmark = pytest.mark.skipif(not PATH.exists(), reason="run scripts/build_unified_catalogue.py first")


@pytest.fixture(scope="module")
def programs():
    return json.loads(PATH.read_text(encoding="utf-8"))["programs"]


def test_only_five_countries_and_app_degree_levels(programs):
    assert {p["country"] for p in programs} <= {"KR", "US", "GB", "NL", "IE"}
    assert {p["degreeLevel"] for p in programs} <= {"undergraduate", "master", "phd"}


def test_every_programme_has_engineering_field_source_and_link(programs):
    for p in programs:
        assert p["engineeringFields"] and set(p["engineeringFields"]) <= FIELDS, p["programId"]
        assert p["source"] in {"team_verified", "official_dataset", "web_verified"}, p["programId"]
        assert p["sourceUrl"], p["programId"]
        assert p["universityKey"], p["programId"]


def test_programme_ids_are_unique(programs):
    ids = [p["programId"] for p in programs]
    assert len(ids) == len(set(ids))


def test_no_foreign_institutions_inside_us_data(programs):
    assert not any(p["universityKey"].endswith(":NA") for p in programs)


def test_difficulty_and_tuition_are_well_formed(programs):
    for p in programs:
        d = p.get("difficultyPercentile")
        assert d is None or 0 <= d <= 100
        if d is not None:
            assert p.get("difficultyBasis"), p["programId"]
        t = p.get("tuition")
        if t and t.get("amount") is not None:
            assert t["currency"] in {"USD", "KRW", "GBP", "EUR"} and t["period"] in {"semester", "year", "total"}


def test_korean_flagships_rank_above_mid_tier(programs):
    """Guards the difficulty indicator choice recorded in docs/ARCHITECTURE.md."""
    index = {p["universityName"]: p["difficultyPercentile"] for p in programs if p["country"] == "KR" and p.get("difficultyPercentile") is not None}
    assert index["서울대학교"] > index["아주대학교"] > index["숭실대학교"]
    assert index["한국과학기술원"] > index["아주대학교"]
