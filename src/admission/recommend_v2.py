"""Recommendation rules added on 2026-11-14 (SPEC F06-F09, AC21-AC27).

Implemented step by step against tests/harness/recommend_v2_cases.yaml.
Step 5: detect_language (AC21).
"""

from __future__ import annotations

import re

HANGUL = re.compile(r"[가-힣ㄱ-ㆎ]")
LATIN = re.compile(r"[A-Za-z]")


def _language_of(text: str) -> str | None:
    """Return "ko" or "en" for one message, or None when it has no letters (e.g. "4.5", "KR")."""
    hangul = len(HANGUL.findall(text or ""))
    latin = len(LATIN.findall(text or ""))
    if hangul == 0 and latin <= 3:  # numbers or short codes like "KR", "MM" say nothing about language
        return None
    return "ko" if hangul >= 0.3 * (hangul + latin) else "en"


def detect_language(messages: list[str], default: str = "en") -> str:
    """Language of the user's latest message that has words (AC21).

    Mixed history follows the last message; a short answer such as "4.5" or "KR"
    keeps the language of the message before it.
    """
    for message in reversed(messages):
        language = _language_of(message)
        if language:
            return language
    return default
