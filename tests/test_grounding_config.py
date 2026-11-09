import json
from pathlib import Path

from admission.official_sources import (
    is_allowed_source,
    load_allowed_hosts,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "grounding_sources.json"


def test_config_covers_five_countries() -> None:
    """출처 설정에 5개국과 중복 없는 ID가 있는지 검사한다."""
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    sources = config["sources"] + config["universitySources"]

    assert {source["country"] for source in sources} == {
        "KR", "US", "GB", "NL", "IE"
    }

    ids = [source["sourceId"] for source in sources]
    assert len(ids) == len(set(ids))
    assert config["retrievalTopK"] == 5


def test_representative_sources_are_allowed() -> None:
    """국가별 대표 호스트가 설정에서 허용되는지 검사한다."""
    hosts = load_allowed_hosts(CONFIG)

    urls = [
        "https://www.data.go.kr/",
        "https://collegescorecard.ed.gov/",
        "https://www.discoveruni.gov.uk/",
        "https://onderwijsdata.duo.nl/",
        "https://www.qualifax.ie/",
        "https://www.universityofgalway.ie/",
    ]

    for url in urls:
        assert is_allowed_source(url, hosts), url


def test_unregistered_sources_are_rejected() -> None:
    """미등록 사이트와 공식 도메인을 흉내 낸 URL을 거부한다."""
    hosts = load_allowed_hosts(CONFIG)

    urls = [
        "https://unregistered.example/",
        "https://www.data.go.kr.evil.example/",
        "https://evil.example/?source=https://www.qualifax.ie",
    ]

    for url in urls:
        assert not is_allowed_source(url, hosts), url