import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "collect_researchers_openalex.py"
spec = importlib.util.spec_from_file_location("collect_researchers_openalex", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

INST = "https://openalex.org/I1"


def topic(name, field, subfield, count=10):
    return {"display_name": name, "count": count,
            "field": {"display_name": field}, "subfield": {"display_name": subfield}}


def author(aid, topics, inst=INST):
    return {"id": f"https://openalex.org/{aid}", "display_name": aid, "works_count": 50,
            "cited_by_count": 100, "summary_stats": {"h_index": 10},
            "last_known_institutions": [{"id": inst}], "topics": topics}


AUTHORS = [
    author("A1", [topic("ML", "Computer Science", "Artificial Intelligence")]),
    author("A2", [topic("Power", "Engineering", "Electrical and Electronic Engineering")]),
    author("A3", [topic("Cells", "Biochemistry", "Cell Biology")]),
    author("A4", [topic("ML", "Computer Science", "Artificial Intelligence")], inst="https://openalex.org/I9"),
    author("A5", [topic("Vision", "Computer Science", "Computer Vision")]),
]


def fake_fetch(path, params):
    if path == "/institutions":
        return {"results": [{"id": INST, "display_name": "Ajou University", "ror": "r"}]}
    if path == "/authors":
        return {"results": AUTHORS}
    if path == "/works":
        return {"results": [{"id": "W1", "title": "Paper", "publication_year": 2025, "doi": None,
                             "authorships": [{"author": {"id": "https://openalex.org/A1"}}],
                             "primary_topic": {"display_name": "ML"}}]}
    raise AssertionError(path)


def test_classify_author():
    assert mod.classify_author(AUTHORS[0]) == "computing"
    assert mod.classify_author(AUTHORS[1]) == "electrical_electronic"
    assert mod.classify_author(AUTHORS[2]) is None


def test_collect_filters_members_fields_and_limit():
    inst, recs = mod.collect(fake_fetch, [("Ajou University", "KR")], per_field=1, pages=1,
                             since="2022-01-01", works_per_author=5, today="2026-11-11", log=lambda *_: None)
    ids = {r["researcherId"] for r in recs}
    assert ids == {"A1", "A2"}  # A3 not engineering, A4 elsewhere, A5 over per_field limit
    a1 = next(r for r in recs if r["researcherId"] == "A1")
    assert a1["recentWorks"][0]["title"] == "Paper"
    assert all(r["role"] == "unverified_researcher" and r["verificationStatus"] == "needs_review" for r in recs)
    assert inst[0]["needsReview"] is False


def test_missing_institution_is_skipped():
    inst, recs = mod.collect(lambda p, q: {"results": []}, [("Nowhere", "KR")], 1, 1,
                             "2022-01-01", 5, "2026-11-11", log=lambda *_: None)
    assert recs == [] and inst[0]["needsReview"] is True
