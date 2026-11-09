import signal
from pathlib import Path


def stop_waiting(signum, frame):
    raise TimeoutError("30초 동안 완료되지 않았습니다.")


signal.signal(signal.SIGALRM, stop_waiting)
signal.alarm(30)

try:
    print("1. Loading SDK...", flush=True)

    from dotenv import dotenv_values
    from google import genai

    settings = dotenv_values(Path(__file__).with_name(".env"))
    print("2. Settings loaded:", settings.get("GEMINI_MODEL"), flush=True)

    with genai.Client(api_key=settings["GEMINI_API_KEY"]) as client:
        print("3. Sending request...", flush=True)

        response = client.models.generate_content(
    model=settings["GEMINI_MODEL"],
    contents="Reply with only: Connection OK",
)

    print("4. Response:", response.text, flush=True)

except Exception as error:
    print("Error type:", type(error).__name__, flush=True)
    print("Detail:", str(error), flush=True)

finally:
    signal.alarm(0)