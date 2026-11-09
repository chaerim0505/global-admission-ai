import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from dotenv import dotenv_values


ROOT = Path(__file__).resolve().parent
settings = dotenv_values(ROOT / ".env")

APIS = [
    (
        "University information",
        "https://api.data.go.kr/openapi/tn_pubr_public_univ_info_api",
        "DATA_GO_KR_UNIV_KEY",
    ),
    (
        "Major information",
        "https://api.data.go.kr/openapi/tn_pubr_public_univ_major_api",
        "DATA_GO_KR_MAJOR_KEY",
    ),
]


def check_api(label, endpoint, key_name):
    key = settings.get(key_name)

    if not key or not key.strip():
        print(f"{label}: missing {key_name}")
        return

    key = key.strip()

    query = urlencode({
        "serviceKey": key,
        "pageNo": 1,
        "numOfRows": 3,
        "type": "json",
    })

    print(f"\n[{label}] Sending request...", flush=True)

    try:
        with urlopen(f"{endpoint}?{query}", timeout=30) as response:
            raw = response.read().decode("utf-8-sig")

        safe_raw = raw.replace(key, "[REDACTED]")

        try:
            data = json.loads(safe_raw)
        except json.JSONDecodeError:
            print("Non-JSON response:")
            print(safe_raw[:2000])
            return

        print(json.dumps(data, ensure_ascii=False, indent=2))

    except HTTPError as error:
        print("HTTP error:", error.code)

    except URLError as error:
        reason = error.reason
        print("Error type:", type(reason).__name__)

        if isinstance(reason, BaseException):
            detail = str(reason).replace(key, "[REDACTED]")
            print("Detail:", detail)
        else:
            print("Detail: Network connection could not be established.")

    except TimeoutError:
        print("Error type: TimeoutError")
        print("Detail: No response within 30 seconds.")


if __name__ == "__main__":
    for label, endpoint, key_name in APIS:
        check_api(label, endpoint, key_name)