"""Find a programme's admission requirements on the university's official site (Gemini + Google Search).

Used for the result cards so each one shows what an applicant needs, with official links.
Rules (SPEC F02, AC10, AC23):
- Every value must come with an https link on the university's official domain; values whose
  link is missing or off-domain are dropped, never guessed.
- Model output is data only; instructions inside it are ignored (AC10).
- These values describe requirements; they never remove a programme from the results (AC6
  exclusions need team-checked data).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIELDS = ("academicRequirement", "minimumGpa", "languageRequirements", "tuition",
          "applicationDeadline", "requiredDocuments", "intake")


def build_prompt(program: dict, context: dict, domain: str) -> str:
    university = program.get("universityNameEnglish") or program["universityName"]
    degree = {"undergraduate": "undergraduate (bachelor's)", "master": "master's", "phd": "PhD"}.get(
        program.get("degreeLevel"), program.get("degreeLevel"))
    return f"""Find the admission requirements for INTERNATIONAL applicants to this programme.
University: {university}
Programme: {program.get("programName")}
Degree: {degree}
Country: {program.get("country")}
Next intake: 2027

Use ONLY pages on the official university domain {domain} (and its subdomains).
Return ONE JSON object and nothing else. Use null when the official site does not say it.
Every non-null value must have its page in "sources".
"programPageUrl" must be the official page of THIS programme at THIS degree level
(the department/programme page or its admissions page), not the university home page.
{{
  "programPageUrl": "https://... official page of this programme" or null,
  "academicRequirement": "short text, e.g. high school diploma / bachelor's in a related field",
  "minimumGpa": {{"value": number, "scale": number}} or null,
  "languageRequirements": [{{"testType": "IELTS|TOEFL_iBT|TOPIK|Duolingo|other", "minimumScore": number, "note": "short"}}],
  "tuition": {{"amount": number, "currency": "USD|GBP|EUR|KRW", "period": "year|semester|total"}} or null,
  "applicationDeadline": "YYYY-MM-DD or short text" or null,
  "requiredDocuments": ["short item", "..."],
  "intake": "e.g. 2027 Fall" or null,
  "sources": {{"<field name>": "https://official page"}}
}}"""


def parse_object(text: str | None) -> dict:
    text = text or ""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    candidate = fenced.group(1) if fenced else text[text.find("{"): text.rfind("}") + 1]
    try:
        value = json.loads(candidate)
    except (json.JSONDecodeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _on_domain(url: str, domain: str) -> bool:
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    domain = domain.lower().removeprefix("www.")
    return url.startswith("https://") and bool(domain) and (host == domain or host.endswith("." + domain))


def normalize(raw: dict, domain: str) -> dict:
    """Keep only fields whose source link is on the official domain (AC23)."""
    sources = raw.get("sources") if isinstance(raw.get("sources"), dict) else {}
    out: dict = {"sources": {}}
    page = str(raw.get("programPageUrl") or "")
    if _on_domain(page, domain) and urlparse(page).path.strip("/"):
        out["programPageUrl"] = page  # a real page on the official site, not the bare home page
    for field in FIELDS:
        value = raw.get(field)
        url = str(sources.get(field) or "")
        if value in (None, "", [], {}) or not _on_domain(url, domain):
            continue
        if field == "minimumGpa":
            if not isinstance(value, dict) or not isinstance(value.get("value"), (int, float)) or not isinstance(value.get("scale"), (int, float)):
                continue
            out["minimumGpa"], out["minimumGpaScale"] = float(value["value"]), float(value["scale"])
        elif field == "languageRequirements":
            items = [v for v in value if isinstance(v, dict) and isinstance(v.get("minimumScore"), (int, float))] if isinstance(value, list) else []
            if not items:
                continue
            out[field] = [{"testType": str(v.get("testType", "")), "minimumScore": float(v["minimumScore"]),
                           "note": str(v.get("note") or "")[:120]} for v in items[:4]]
        elif field == "tuition":
            if not isinstance(value, dict) or not isinstance(value.get("amount"), (int, float)):
                continue
            out[field] = {"amount": float(value["amount"]), "currency": str(value.get("currency") or ""),
                          "period": str(value.get("period") or "year"), "basis": "official programme page"}
        elif field == "requiredDocuments":
            if not isinstance(value, list):
                continue
            out[field] = [str(v)[:100] for v in value if str(v).strip()][:8]
        else:
            out[field] = str(value)[:300]
        out["sources"][field] = url
    return out


def find_requirements(program: dict, context: dict, domain: str, client=None) -> dict:
    if not domain:
        return {"sources": {}}
    if client is None:
        from dotenv import load_dotenv
        from google import genai
        from google.genai import types as genai_types

        load_dotenv(PROJECT_ROOT / ".env")
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing.")
        client = genai.Client(api_key=api_key, http_options=genai_types.HttpOptions(timeout=60_000))
    from google.genai import types

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        contents=build_prompt(program, context, domain),
        config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())], temperature=0),
    )
    return normalize(parse_object(response.text), domain)
