from pathlib import Path
import ast

path = Path('frontend/app.py')
original = path.read_text(encoding='utf-8')
ast.parse(original)
if 'def show_official_search(' in original:
    print('Gemini search already installed')
    raise SystemExit(0)

addition = '''def show_official_search(program: dict) -> None:
    """On-demand Gemini research; does not modify verified catalogue data."""
    import hashlib
    import os
    from urllib.parse import urlparse

    uid = hashlib.sha256(str(program.get("programId", program)).encode()).hexdigest()[:16]
    state_key = "official_search_" + uid
    if st.button("🔎 Search official admission requirements", key="official_btn_" + uid):
        try:
            from dotenv import load_dotenv
            load_dotenv(ROOT / ".env")
            from google import genai
            from google.genai import types
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
            source = str(program.get("sourceUrl") or "")
            host = urlparse(source).hostname
            if not api_key:
                raise ValueError("GEMINI_API_KEY missing in .env")
            if not source.startswith("https://") or not host:
                raise ValueError("Official HTTPS source URL missing")
            prompt = (
                "Find current admission requirements on official university websites. "
                "Give the official URL and academic year for each factual claim. "
                "Do not invent GPA, language scores, deadlines, tuition, or scholarships. "
                "Mark missing information NOT VERIFIED. Do not predict admission probability. "
                f"University: {program.get('universityName')}; "
                f"Programme: {program.get('programName')}; "
                f"Degree: {program.get('degreeLevel')}; official starting URL: {source}. "
                "Prefer the university domain " + host + ". Reply in Korean."
            )
            with st.spinner("Searching official admission sources..."):
                response = genai.Client(api_key=api_key).models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                        temperature=0,
                    ),
                )
            sources = []
            if response.candidates:
                meta = getattr(response.candidates[0], "grounding_metadata", None)
                for chunk in (getattr(meta, "grounding_chunks", None) or []):
                    web = getattr(chunk, "web", None)
                    if web and getattr(web, "uri", None):
                        sources.append((web.title or "Search citation", web.uri))
            st.session_state[state_key] = {
                "text": response.text or "No response text",
                "sources": sources,
                "model": model,
            }
        except Exception as exc:
            msg = str(exc)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                msg = "Gemini API quota exceeded (429). Existing recommendations remain available."
            st.session_state[state_key] = {"error": msg}

    result = st.session_state.get(state_key)
    if not result:
        return
    if result.get("error"):
        st.warning(result["error"])
        return
    st.caption("Gemini model: " + result["model"])
    if not result["sources"]:
        st.warning("No search citations returned. This answer is not verified.")
    else:
        st.info("AI research with citations; individual requirements still need verification.")
    st.markdown(result["text"])
    if result["sources"]:
        with st.expander("Search citations"):
            for url, title in dict((url, title) for title, url in result["sources"]).items():
                st.markdown(f"- [{title}]({url})")


'''

# Insert at a top-level function boundary, never inside another function.
needle = 'def show_results('
if original.count(needle) != 1:
    raise RuntimeError('Expected exactly one show_results function')
source = original.replace(needle, addition + needle, 1)
lines = source.splitlines(keepends=True)
tree = ast.parse(source)
results = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'show_results')
card_calls = [n for n in ast.walk(results) if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name) and n.value.func.id == 'show_card']
if len(card_calls) != 1:
    raise RuntimeError('Expected exactly one show_card call')
call = card_calls[0]
indent = lines[call.lineno - 1][:len(lines[call.lineno - 1]) - len(lines[call.lineno - 1].lstrip())]
lines.insert(call.end_lineno, indent + 'show_official_search(program)\n')
source = ''.join(lines)
compile(source, str(path), 'exec')
backup = path.with_name('app.py.before_gemini')
if not backup.exists():
    backup.write_text(original, encoding='utf-8')
path.write_text(source, encoding='utf-8')
print('SUCCESS: Gemini official search connected')
print('Model setting unchanged; backup:', backup)
