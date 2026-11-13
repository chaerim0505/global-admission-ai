"""Download Korean university and department standard data from data.go.kr.

Run on your Mac (the API is not reachable from Claude's workspace):

    python3 scripts/fetch_kr_univ_api.py --test      # 3 rows each, prints field names
    python3 scripts/fetch_kr_univ_api.py             # everything

Reads DATA_GO_KR_UNIV_KEY and DATA_GO_KR_MAJOR_KEY (or DATA_GO_KR_API_KEY) from .env.
Saves raw rows to data/raw/kr_api/univ_info.json and univ_major.json.
Standard library only.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "kr_api"
BASE = "https://api.data.go.kr/openapi/"
APIS = {
    "univ_info": ("tn_pubr_public_univ_info_api", "DATA_GO_KR_UNIV_KEY"),
    "univ_major": ("tn_pubr_public_univ_major_api", "DATA_GO_KR_MAJOR_KEY"),
}


def load_env() -> None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"'))


def fetch_page(endpoint: str, key: str, page: int, rows: int) -> dict:
    query = urllib.parse.urlencode({"pageNo": page, "numOfRows": rows, "type": "json"})
    url = f"{BASE}{endpoint}?serviceKey={key}&{query}"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                text = response.read().decode("utf-8")
            return json.loads(text)
        except json.JSONDecodeError:
            raise SystemExit(f"Not JSON (key not active yet?):\n{text[:500]}")
        except Exception as error:
            if attempt == 2:
                raise SystemExit(f"Request failed: {error}")
            time.sleep(3)
    return {}


def body_of(data: dict) -> dict:
    response = data.get("response", data)
    header = response.get("header", {})
    if header and str(header.get("resultCode")) not in ("00", "0"):
        raise SystemExit(f"API error: {header}")
    return response.get("body", {})


def items_of(body: dict) -> list[dict]:
    items = body.get("items", [])
    if isinstance(items, dict):
        items = items.get("item", [])
    return [items] if isinstance(items, dict) else list(items)


def main() -> int:
    load_env()
    test = "--test" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (endpoint, env_name) in APIS.items():
        key = os.getenv(env_name) or os.getenv("DATA_GO_KR_API_KEY")
        if not key:
            print(f"Missing {env_name} in .env")
            return 1
        rows = 3 if test else 1000
        first = body_of(fetch_page(endpoint, key, 1, rows))
        items = items_of(first)
        total = int(first.get("totalCount") or len(items))
        print(f"{name}: totalCount={total}")
        if test:
            print("  fields:", list(items[0].keys()) if items else "(no rows)")
            print("  sample:", json.dumps(items[:1], ensure_ascii=False)[:800])
            continue
        page = 1
        while len(items) < total:
            page += 1
            more = items_of(body_of(fetch_page(endpoint, key, page, rows)))
            if not more:
                break
            items.extend(more)
            print(f"  page {page}: {len(items)}/{total}")
            time.sleep(0.3)
        (OUT / f"{name}.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  saved {len(items)} rows to {OUT / (name + '.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
