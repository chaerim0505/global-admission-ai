import os
import re
from pathlib import Path

from dotenv import dotenv_values
from google import genai
from google.genai import types


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SYSTEM_PROMPT = """
너는 대학 과정 추천 이유를 자연스러운 한국어로 다듬는 작성기다.

규칙:
- 주어진 초안의 사실만 사용한다. 새 숫자, 대학명, 장학금, 날짜를 추가하지 않는다.
- "확인 필요"가 있으면 지원 가능하다고 단정하지 않는다.
- 합격 가능성이나 확률을 말하지 않는다.
- 3문장 이내로 쓴다.
"""

NUMBER = re.compile(r"\d+(?:\.\d+)?")


def gemini_reason(candidate: dict, draft: str) -> str:
    settings = dotenv_values(PROJECT_ROOT / ".env")
    api_key = settings.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    model = settings.get("GEMINI_MODEL") or os.getenv("GEMINI_MODEL")

    if not api_key or not model:
        raise RuntimeError("Gemini API 키 또는 모델 설정이 없습니다.")

    with genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=20_000),
    ) as client:
        response = client.models.generate_content(
            model=model,
            contents=f"초안:\n{draft}",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0,
            ),
        )

    text = (response.text or "").strip()

    # Reject any wording that adds numbers missing from the draft.
    if not text or not set(NUMBER.findall(text)) <= set(NUMBER.findall(draft)):
        raise ValueError("추천 이유에 초안에 없는 숫자가 있습니다.")

    return text
