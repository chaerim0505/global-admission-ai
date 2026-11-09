import json
from pathlib import Path

import pytest

from admission.official_sources import (
    is_allowed_source,
    load_allowed_hosts,
)


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://www.example.edu/admissions", True),
        ("https://WWW.EXAMPLE.EDU/fees", True),
        ("https://www.example.edu:443/fees", True),
        ("http://www.example.edu/fees", False),
        ("https://www.example.edu.evil.test/fees", False),
        ("https://evil.test/?url=https://www.example.edu", False),
        ("https://www.example.edu@evil.test/fees", False),
        ("https://user@www.example.edu/fees", False),
        ("https://www.example.edu:8080/fees", False),
        ("not-a-url", False),
    ],
)
def test_source_url(url: str, expected: bool) -> None:
    """正規ホストと偽装URLを区別する。"""
    allowed = {"www.example.edu"}

    assert is_allowed_source(url, allowed) is expected


def test_load_hosts_from_both_groups(tmp_path: Path) -> None:
    """기관과 대학의 허용 호스트를 함께 읽는다."""
    path = tmp_path / "sources.json"
    path.write_text(
        json.dumps({
            "sources": [
                {"allowedHosts": ["api.example.org"]}
            ],
            "universitySources": [
                {"allowedHosts": ["www.example.edu"]}
            ],
        }),
        encoding="utf-8",
    )

    assert load_allowed_hosts(path) == {
        "api.example.org",
        "www.example.edu",
    }
def test_candidate_with_unregistered_source_is_held() -> None:
    """미등록 출처의 후보를 검증 보류한다."""
    from admission.source_validator import enforce_official_sources

    candidates = [
        {
            "programId": "allowed",
            "fieldClassification": {
                "sourceUrl": "https://official.example/program"
            },
        },
        {
            "programId": "held",
            "fieldClassification": {
                "sourceUrl": "https://unregistered.example/program"
            },
        },
    ]

    clean, issues = enforce_official_sources(
        candidates,
        {"official.example"},
    )

    assert [item["programId"] for item in clean] == ["allowed"]
    assert issues == [{
        "programId": "held",
        "problem": "unregistered_source",
    }]