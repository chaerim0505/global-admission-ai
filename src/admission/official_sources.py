import json
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config" / "grounding_sources.json"


def load_allowed_hosts(path: Path = DEFAULT_CONFIG) -> set[str]:
    """설정에 명시된 공식 호스트 이름을 읽는다."""
    config = json.loads(path.read_text(encoding="utf-8"))
    hosts: set[str] = set()

    for group in ("sources", "universitySources"):
        for source in config.get(group, []):
            for host in source.get("allowedHosts", []):
                hosts.add(host.strip().lower())

    return hosts


def is_allowed_source(url: str, allowed_hosts: set[str]) -> bool:
    """HTTPS URL의 호스트가 허용 목록과 정확히 일치하는지 검사한다."""
    try:
        parsed = urlsplit(url)

        if parsed.scheme != "https":
            return False

        if parsed.username is not None or parsed.password is not None:
            return False

        if parsed.port not in (None, 443):
            return False

        host = parsed.hostname
        if host is None:
            return False

        return host.lower() in allowed_hosts

    except ValueError:
        return False