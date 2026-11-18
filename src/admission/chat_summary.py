"""채팅 답변을 결과 탭과 같은 추천 결과로 만든다 (D2).

채팅과 결과 탭이 서로 다른 데이터로 계산해 "0개"와 "2개"처럼 다른 답을 하던 문제를 막는다.
- 채팅 요약은 결과 탭이 쓰는 recommend_v2 결과(results, shortfallReason)만 받아 문장으로 바꾼다.
- 모든 문장은 화면 언어(en/ko)를 따른다 (AC21).
- 채팅에 보내는 이전 조건에는 오른쪽 폼에 이미 입력된 값을 합쳐, 같은 질문을 반복하지 않게 한다.
"""

from __future__ import annotations

SUPPORTED = ("KR", "US", "GB", "NL", "IE")

TEXT = {
    "found": {
        "en": "I found {n} universities for your conditions.",
        "ko": "조건에 맞는 대학 {n}곳을 찾았어요.",
    },
    "found_one": {
        "en": "I found 1 university for your conditions.",
        "ko": "조건에 맞는 대학 1곳을 찾았어요.",
    },
    "none": {
        "en": "No universities matched every condition. Conditions were not relaxed. "
              "Try changing the country, field or budget.",
        "ko": "모든 조건에 맞는 대학을 찾지 못했어요. 조건은 완화하지 않았습니다. "
              "국가, 분야, 예산을 바꿔 다시 검색해 보세요.",
    },
    "shortfall": {
        "en": "Fewer than five universities meet every condition. Conditions were not relaxed.",
        "ko": "모든 조건을 만족하는 대학이 5곳보다 적습니다. 조건은 완화하지 않았습니다.",
    },
    "web_note": {
        "en": "Web search results are not yet verified. Check each official page.",
        "ko": "웹 검색 결과는 아직 검증되지 않았어요. 각 공식 페이지에서 확인하세요.",
    },
    "see_results": {
        "en": "→ Open the Results tab for details and official links.",
        "ko": "→ 자세한 내용과 공식 링크는 Results 탭에서 확인하세요.",
    },
    "web": {"en": "Found by web search", "ko": "웹 검색으로 찾음"},
    "unsupported": {
        "en": "{names} is not supported yet. We cover Korea, the US, the UK, the Netherlands and Ireland.",
        "ko": "{names}은(는) 아직 지원하지 않아요. 한국, 미국, 영국, 네덜란드, 아일랜드만 지원합니다.",
    },
}

TIERS = {
    "reach": {"en": "Reach", "ko": "상향"},
    "match": {"en": "Match", "ko": "적정"},
    "safety": {"en": "Safety", "ko": "안정"},
}


def _say(key: str, lang: str, **values) -> str:
    entry = TEXT[key]
    return (entry.get(lang) or entry["en"]).format(**values)


def build_summary(results: list[dict], shortfall: bool, lang: str = "en",
                  web_notice: str | None = None) -> str:
    """Summarise the same results the Results tab shows."""
    lang = lang if lang in ("en", "ko") else "en"
    if not results:
        lines = [_say("none", lang)]
        if web_notice:
            lines.append(web_notice)
        return "\n".join(lines)

    lines = [_say("found_one", lang) if len(results) == 1 else _say("found", lang, n=len(results)), ""]
    has_web = False
    for number, item in enumerate(results, 1):
        parts = [str(item.get("universityName") or "").strip()]
        if item.get("programName"):
            parts.append(str(item["programName"]).strip())
        tier = TIERS.get(item.get("admissionTier"))
        if tier:
            parts.append(tier[lang])
        if str(item.get("source", "")).startswith("web"):
            parts.append(_say("web", lang))
            has_web = True
        lines.append(f"{number}. " + " · ".join(p for p in parts if p))

    lines.append("")
    if shortfall:
        lines.append(_say("shortfall", lang))
    if has_web:
        lines.append(_say("web_note", lang))
    if web_notice:
        lines.append(web_notice)
    lines.append("")
    lines.append(_say("see_results", lang))
    return "\n".join(lines)


def unsupported_countries(codes) -> list[str]:
    """Requested country codes outside the five supported countries."""
    seen = []
    for code in codes or []:
        value = str(code).strip().upper()
        if value and value not in SUPPORTED and value not in seen:
            seen.append(value)
    return seen


def unsupported_message(names: list[str], lang: str = "en") -> str:
    return _say("unsupported", lang if lang in ("en", "ko") else "en", names=", ".join(names))


def merge_previous_context(agent_context: dict | None, form_values: dict) -> dict:
    """Context sent with the next chat message: chat answers plus values already in the form.

    Form values win, so the chat does not ask again for something the user already entered.
    Empty values (None, "", []) are ignored.
    """
    merged = dict(agent_context or {})
    for key, value in form_values.items():
        if value is None or value == "" or value == []:
            continue
        merged[key] = value
    return merged
