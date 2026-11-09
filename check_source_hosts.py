import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent


def collect_source_urls(value: object) -> list[str]:
    """중첩 데이터에서 sourceUrl 값을 수집한다."""
    urls: list[str] = []

    if isinstance(value, dict):
        for key, item in value.items():
            if key == "sourceUrl" and isinstance(item, str):
                urls.append(item)
            else:
                urls.extend(collect_source_urls(item))

    elif isinstance(value, list):
        for item in value:
            urls.extend(collect_source_urls(item))

    return urls


def main() -> None:
    """현재 과정 데이터에 사용된 출처 호스트를 출력한다."""
    path = ROOT / "data" / "programs.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    counts: Counter[str] = Counter()

    for url in collect_source_urls(data):
        try:
            host = urlsplit(url).hostname
        except ValueError:
            host = None

        counts[host or "(invalid URL)"] += 1

    print(f"Program records: {len(data)}")
    print("Source hosts:")

    for host, count in sorted(counts.items()):
        print(f"{host}: {count}")


if __name__ == "__main__":
    main()