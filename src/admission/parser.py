import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

from admission.schemas import RequestContext


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "parse_query.md"


def load_system_prompt(path: Path = PROMPT_PATH) -> str:
    """parse_query.md의 '---' 아래 본문을 시스템 프롬프트로 읽는다."""
    text = path.read_text(encoding="utf-8")
    return text.split("\n---\n", 1)[1] if "\n---\n" in text else text


SYSTEM_PROMPT = load_system_prompt()


def _with_questions(text: str, questions: list[str] | None) -> str:
    """Give the model the question the user is answering."""
    if not questions:
        return text
    asked = "\n".join(f"- {question}" for question in questions)
    return f"[직전 질문]\n{asked}\n\n[사용자 답변]\n{text}"


def parse_query(
    text: str,
    pending_questions: list[str] | None = None,
) -> RequestContext:
    if not text.strip():
        raise ValueError("입력 문장이 비어 있습니다.")

    load_dotenv(PROJECT_ROOT / ".env")

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL")
    if not api_key or not model:
        raise RuntimeError("Gemini API 키 또는 모델 설정이 없습니다.")

    with genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=60_000,
            retry_options=types.HttpRetryOptions(
                attempts=3,
                http_status_codes=[429, 500, 502, 503, 504],
                initial_delay=2,
                max_delay=10,
                jitter=1,
    ),
),
    ) as client:
        response = client.models.generate_content(
            model=model,
            contents=_with_questions(text, pending_questions),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_json_schema=RequestContext.model_json_schema(),
                thinking_config=types.ThinkingConfig(
                    thinking_level="low",
                ),
            ),
        )

    if not response.text:
        raise RuntimeError("모델이 JSON 응답을 반환하지 않았습니다.")

    return RequestContext.model_validate_json(response.text)