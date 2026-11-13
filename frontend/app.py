
"""Bilingual Admission AI sample frontend."""
import os
import html
import json
import sqlite3
from pathlib import Path

import streamlit as st

from translations import KO
from admission_2027_panel import show_2027_panel
import requests

def _secret(name: str, default: str) -> str:
    """Read a Streamlit secret, falling back to the environment when no secrets.toml exists (local runs)."""
    try:
        return st.secrets.get(name, os.getenv(name, default))
    except Exception:  # StreamlitSecretNotFoundError when running locally without secrets.toml
        return os.getenv(name, default)


API_BASE_URL = _secret("API_BASE_URL", "http://127.0.0.1:8001").rstrip("/")


ROOT = Path(__file__).resolve().parents[1]

# AI 탐색(검증 전) 규칙은 백엔드 패키지 한 곳에서 관리한다 (SPEC AC19).
import sys  # noqa: E402

if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from admission.ai_exploration import explore_programmes  # noqa: E402
from admission.requirement_finder import find_requirements  # noqa: E402
from admission.recommend_v2 import (  # noqa: E402
    detect_language,
    load_catalogue as _load_catalogue,
    official_domains,
    recommend as recommend_v2,
    requirement_status,
    scholarships_for,
    web_results_from_gemini,
)


@st.cache_resource(show_spinner=False)
def load_unified_catalogue() -> list[dict]:
    return _load_catalogue()
DATABASE_PATH = ROOT / "database" / "admission_catalogue.sqlite"

COUNTRIES = {
    "KR": "South Korea",
    "US": "United States",
    "GB": "United Kingdom",
    "NL": "Netherlands",
    "IE": "Ireland",
}

DEGREES = {
    "undergraduate": "Undergraduate",
    "master": "Master",
    "phd": "PhD",
}

EDUCATION = {
    "high_school": "High school",
    "bachelor": "Bachelor",
    "master": "Master",
}

FIELDS = {
    "computing": "Computing",
    "electrical_electronic": "Electrical & Electronic",
    "mechanical": "Mechanical",
    "civil_environmental": "Civil & Environmental",
    "chemical_materials": "Chemical & Materials",
    "industrial_systems": "Industrial & Systems",
    "aerospace": "Aerospace",
    "biomedical": "Biomedical",
    "other_engineering": "Other engineering",
}

GRADING = {
    "gpa": "GPA",
    "percentage": "Percentage",
    "grade_rank": "Grade rank",
    "total_score": "Total score",
    "other": "Other",
}

PERIODS = {
    "year": "Year",
    "semester": "Semester",
    "total": "Total",
}

CSS = """
<style>
.chat-speaker {
    color: #8591aa;
    font-size: 13px;
    margin: 18px 4px 10px;
}

.chat-bubble {
    padding: 20px 22px;
    border-radius: 18px;
    font-size: 16px;
    line-height: 1.8;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    margin-bottom: 22px;
}

.user-bubble {
    background: #ffffff;
    color: #202b49;
    border: 1px solid #d9e1ef;
    border-bottom-right-radius: 5px;
    box-shadow: 0 3px 12px rgba(32, 43, 73, 0.04);
}

.assistant-bubble {
    background: #e9f0ff;
    color: #344d79;
    border: 1px solid #e9f0ff;
    border-bottom-left-radius: 5px;
}

.chat-empty {
    text-align: center;
    padding: 90px 24px;
    color: #8591aa;
}

.chat-empty h3 {
    font-size: 20px;
    margin-top: 14px;
}

.chat-empty-icon {
    font-size: 36px;
    color: #386be8;
}

div[data-testid="stForm"] {
    background: #ffffff;
    border: 1px solid #dbe3f1;
    border-radius: 16px;
    padding: 12px 14px;
    box-shadow: 0 4px 16px rgba(31, 42, 68, 0.06);
}

div[data-testid="InputInstructions"] {
    display: none;
}

.block-container {
    max-width: 1600px;
    padding-top: 5rem;
    padding-bottom: 3rem;
}

h1, h2, h3 {
    color: #202b49;
    letter-spacing: -0.025em;
}

.topbar {
    display: flex;
    align-items: center;
    gap: 14px;
    background: white;
    padding: 24px 30px;
    border-radius: 20px;
    border: 1px solid #e1e7f1;
    font-size: 26px;
    font-weight: 800;
    margin-bottom: 16px;
}

.logo {
    width: 36px;
    height: 36px;
    border-radius: 11px;
    background: linear-gradient(135deg, #386be8, #62b4df);
}

.muted {
    color: #7885a0;
    font-size: 14px;
}

div[data-testid="stButton"] button,
div[data-testid="stFormSubmitButton"] button {
    border-radius: 12px;
    min-height: 44px;
}

.card {
    background: white;
    border: 1px solid #dce3f0;
    border-radius: 18px;
    padding: 26px;
    margin-bottom: 18px;
}

.card h3 {
    margin: 0 0 8px;
    font-size: 22px;
}

.reason {
    background: #f3f6fd;
    border-radius: 12px;
    padding: 14px 16px;
    margin: 18px 0;
    color: #405477;
}

.details {
    display: grid;
    grid-template-columns: 1.2fr 1fr;
    gap: 24px;
}

.requirement {
    padding: 12px 0;
    border-bottom: 1px dashed #e1e7f1;
    font-size: 14px;
}

.badge {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
    background: #fff3db;
    color: #a46a12;
}

.box {
    border: 1px solid #e4e9f2;
    border-radius: 12px;
    padding: 14px;
    margin: 8px 0 16px;
}

.source {
    border-top: 1px solid #edf0f6;
    padding-top: 14px;
    margin-top: 16px;
    font-size: 13px;
    color: #7885a0;
}

.source a {
    color: #386be8;
}

@media (max-width: 750px) {
    .details {
        grid-template-columns: 1fr;
    }
}
</style>
"""


# Follow-up questions keyed by field, in English; t() gives the Korean version (AC21).
FOLLOW_UP_QUESTIONS = {
    "applicantType": "Which degree are you applying for: undergraduate, master's or PhD?",
    "currentEducationLevel": "What is your current or highest level of education?",
    "transcriptCountry": "Which country issued your transcript?",
    "academicScore": "What is your current or final school grade?",
    "gradingSystem": "Which grading system is it: GPA, percentage, grade or total score?",
    "maximumScore": "What is the maximum possible score for that grade?",
    "interests": "Which engineering field or research area are you interested in?",
    "engineeringFields": "Which engineering field are you interested in?",
    "tuitionCurrency": "What currency is your maximum tuition in? e.g. EUR, USD, KRW",
    "tuitionPeriod": "Is your maximum tuition per semester, per year or for the whole programme?",
    "maximumTuition": "What is the most tuition you can afford?",
}


WORLD_COUNTRIES = json.loads(
    (ROOT / "data" / "reference" / "countries.json").read_text(encoding="utf-8")
)["countries"]
WORLD_NAMES = {c["code"]: c for c in WORLD_COUNTRIES}


def country_name(code: str | None) -> str:
    """Country name in the current language, with its code (for pickers)."""
    if not code:
        return ""
    item = WORLD_NAMES.get(code)
    if not item:
        return code
    name = item["ko"] if st.session_state.get("ui_language") == "ko" else item["en"]
    return f"{name} ({code})"


def t(text: str) -> str:
    """Translate an interface label into the selected language."""
    if st.session_state.get("ui_language") == "ko":
        return KO.get(text, text)
    return text


def safe(value: object) -> str:
    """Escape text before inserting it into HTML."""
    if value is None:
        value = t("Not recorded")
    return html.escape(str(value))


def label(text: str) -> str:
    """Translate and escape an HTML label."""
    return safe(t(text))


def choice(
    title: str,
    options: dict,
    key: str,
    default: str,
) -> str:
    """Show translated choices while preserving internal values."""
    if key not in st.session_state:
        st.session_state[key] = default

    return st.selectbox(
        t(title),
        list(options),
        format_func=lambda value: t(options[value]),
        key=key,
    )



def load_programs() -> list[dict]:
    """Load integrated programme data."""
    integrated = ROOT / "data" / "programs_integrated.json"

    if integrated.is_file():
        data = json.loads(integrated.read_text(encoding="utf-8"))

        if isinstance(data, list):
            return data

        if isinstance(data, dict) and isinstance(data.get("programs"), list):
            return data["programs"]

        raise ValueError("Invalid integrated programme data")

    if not DATABASE_PATH.is_file():
        raise FileNotFoundError(DATABASE_PATH)

    uri = DATABASE_PATH.resolve().as_uri() + "?mode=ro"

    with sqlite3.connect(uri, uri=True) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT * FROM programs ORDER BY programName, degreeLevel, programId"
        ).fetchall()

    programs = [dict(row) for row in rows]

    for program in programs:
        program["engineeringFields"] = json.loads(
            program["engineeringFields"]
        )

    return programs


def show_ajou_cost_references(reference: dict, degree: str) -> list[dict]:
    """Show guide figures without treating them as programme prices or awards."""
    st.markdown(f'**{t("Tuition reference")}**')
    st.caption(t(
        "The guide lists 2026 fees. Confirm the programme rate and billing period for 2027."
    ))
    engineering_rates = [
        rate
        for rate in reference["tuitionCategories"]
        if rate["field_of_study"] == "Engineering"
    ]
    for rate in engineering_rates:
        currency = rate["currency"]
        st.write(
            f'{t("Engineering tuition")}: {currency} {rate["tuition_amount"]:,} · '
            f'{t("Entrance fee")}: {currency} {rate["entrance_fee_amount"]:,}'
        )

    st.markdown(f'**{t("Scholarship references")}**')
    st.caption(t("Check the official conditions and deadlines for each award."))
    awards = reference["scholarships"]
    guide_degree = {"master": "master", "phd": "doctoral"}[degree]
    for award in awards:
        st.write(award["name"])
        for benefit in award.get("benefits", []):
            if benefit["degree"] == guide_degree:
                coverage = benefit["tuition_coverage_percent"]
                st.write(f'{t("Tuition coverage")}: {coverage}%')
        if award.get("applicant_stage") == "continuing_students":
            st.caption(t("For continuing students after the first semester."))
        if award.get("selection", {}).get("department_recommendation_required"):
            st.caption(t("Department recommendation and committee selection apply."))
        for tier in award.get("benefit_tiers", []):
            minimum = tier.get("TOPIK_minimum_level")
            level = f"≥ {minimum}" if minimum else f'= {tier["TOPIK_exact_level"]}'
            waiver = tier["entrance_fee_waiver_percent"]
            st.write(f'TOPIK {level} · {t("Entrance fee waiver")}: {waiver}%')
        if award.get("required_language_institute"):
            st.caption(t("Requires qualifying study at Ajou’s Korean Language Institute."))

    return engineering_rates + awards


def show_admission_evidence(program_id: str) -> None:
    """Display linked draft evidence without judging eligibility."""
    if show_2027_panel(ROOT, program_id):
        return
    catalogue_path = ROOT / "data" / "catalogue" / "evidence.json"
    catalogue = json.loads(catalogue_path.read_text(encoding="utf-8"))
    if program_id in catalogue:
        item = catalogue[program_id]
        ko = st.session_state.get("ui_language") == "ko"
        st.info("과정 운영 근거를 확인했습니다. 상세 지원 자격과 현재 모집 여부는 확인이 필요합니다." if ko else "Programme existence is documented. Detailed eligibility and current availability still need checking.")
        st.markdown(f'[{"대학 공식 출처" if ko else "Official university source"}]({item["sourceUrl"]})')
        st.caption(("출처 확인일: " if ko else "Source checked: ") + item["checkedAt"])
        if item["admissionRoute"] == "research":
            st.warning("연구과정입니다. 지도교수, 연구계획, 재원 및 모집 공고에 따라 지원 경로가 달라집니다. 현재 모집 중이라는 뜻은 아닙니다." if ko else "Research route: check supervisors, proposals, funding and vacancies. This listing does not imply an open position.")
        for label in (["학력·성적 요건", "어학 요건", "필수 제출 서류", "모집 일정", "학비·장학금"] if ko else ["Academic requirements", "Language requirements", "Required documents", "Application dates", "Tuition and scholarships"]):
            st.write("• " + label + (": 확인 필요 — 공식 출처 참고" if ko else ": needs checking — consult the official source"))
        return
    path = ROOT / "data" / "sample" / "ajou_program_details.json"

    if not path.is_file():
        st.info(
            "Linked admission details are not available."
            if st.session_state.get("ui_language") != "ko"
            else "연결된 입학 정보가 없습니다."
        )
        return

    korean = st.session_state.get("ui_language") == "ko"

    try:
        package = json.loads(path.read_text(encoding="utf-8"))
        matches = [
            item
            for item in package["programDetails"]
            if item["programId"] == program_id
        ]

        if len(matches) != 1:
            st.warning(
                "No unique admission record was found."
                if not korean
                else "일치하는 입학 정보 하나를 찾을 수 없습니다."
            )
            return

        detail = matches[0]
        education = detail["educationRequirement"]
        language = detail["languageRequirement"]
        department = detail["department"]

        st.caption(
            "Draft evidence from the admissions guide. "
            "Check Ajou for updates. Applicant eligibility has not been assessed."
            if not korean
            else "모집요강의 초안 정보입니다. "
            "최신 공지는 아주대학교에서 확인해 주세요. 지원 자격 충족 여부는 판단하지 않았습니다."
        )

        eligibility = detail.get("basicEligibility", [])
        if eligibility:
            st.markdown(f'**{t("Basic eligibility routes")}**')
            st.caption(t("Meet all conditions under one of the listed routes."))
            for rule in eligibility:
                for number, route in enumerate(rule["alternatives"], start=1):
                    st.write(f'{t("Route")} {number}')
                    for condition in route["conditions"]:
                        st.write(f"• {condition}")

        st.markdown("**학력 요건**" if korean else "**Education requirement**")
        degree_labels = {
            "bachelor": "학사" if korean else "Bachelor",
            "master": "석사" if korean else "Master",
        }
        required = degree_labels.get(
            education["required_degree"],
            education["required_degree"],
        )
        st.write(
            f"필요 학위: {required}"
            if korean
            else f"Required degree: {required}"
        )
        st.write(
            f"학위 취득 기한: {education['degree_completion_deadline']}"
            if korean
            else f"Degree completion deadline: {education['degree_completion_deadline']}"
        )

        st.markdown("**어학 요건**" if korean else "**Language requirement**")
        st.write(
            f"어학 그룹: {language['language_group']}"
            if korean
            else f"Language group: {language['language_group']}"
        )

        for test in language["accepted_tests"]:
            minimum = test.get("minimum_score", test.get("minimum_level"))
            st.write(f"• {test['test']}: ≥ {minimum}")

        if language["language_group"] == "A":
            st.caption(
                "These are alternatives; all tests are not required. "
                "An English-medium education exception may apply under "
                "the guide's stated conditions."
                if not korean
                else "시험들은 대체 가능한 선택지이며 모두 제출할 필요는 없습니다. "
                "모집요강의 조건에 따라 영어 수업 이수 증빙 예외가 적용될 수 있습니다."
            )
        else:
            st.caption(
                "TOPIK is required for this group. Some departments or "
                "majors may require a higher level."
                if not korean
                else "이 그룹은 TOPIK이 필요합니다. 일부 학과·전공은 "
                "더 높은 급수를 요구할 수 있습니다."
            )

        st.markdown(
            "**교수 사전 연락**" if korean else "**Professor pre-contact**"
        )
        required_contact = department["professor_precontact_required"]
        st.write(
            ("필수" if required_contact else "이 기록에서는 필수로 표시되지 않음")
            if korean
            else (
                "Required"
                if required_contact
                else "Not marked as required in this record"
            )
        )

        deadlines = detail.get("deadlines", [])
        if deadlines:
            st.markdown(f'**{t("Application schedule")}**')
            events = {
                "online_application": "Online application",
                "document_submission": "Document receipt",
            }
            for deadline in deadlines:
                event = deadline["event"]
                opens = deadline["opens_at_local"].replace("T", " ")
                closes = deadline["deadline_at_local"].replace("T", " ")
                st.write(
                    f'{t(events.get(event, event))}: {opens} – {closes} '
                    f'({deadline["timezone"]})'
                )
            st.caption(t("The university must receive the documents by the deadline."))
            st.link_button(
                t("Official Ajou schedule"),
                "https://ajou.ac.kr/gs_eng/admission/schedule.do",
            )

        st.markdown(
            "**제출 서류 목록**" if korean else "**Document checklist**"
        )
        st.caption(
            "Document names below retain the source-data language. "
            "Check the official guide for originals, translations, and exceptions."
            if not korean
            else "아래 서류명은 원문 데이터의 언어로 표시합니다. "
            "원본, 번역 및 예외 요건은 공식 모집요강에서 확인해 주세요."
        )

        documents = detail["requiredDocuments"]
        for document in documents:
            st.write(f"• {document['document_name']}")
            st.caption(
                f'{document["requirement_condition"]} {document["preparation_notes"]}'
            )

        cost_sources = show_ajou_cost_references(
            package["universityReferenceData"], detail["degreeLevel"]
        )

        st.markdown("**출처 기록**" if korean else "**Source references**")
        records = [education, language, department, *eligibility, *deadlines]
        records.extend(documents + cost_sources)
        source_pages = {
            (record["source_file"], record["source_pdf_page"])
            for record in records
        }
        for filename, page in sorted(source_pages):
            st.caption(f"{filename} · PDF {page}")

    except (OSError, ValueError, KeyError, TypeError) as error:
        st.error(
            "Unable to read linked admission details."
            if not korean
            else "연결된 입학 정보를 읽을 수 없습니다."
        )
        st.code(str(error))




def show_card(program: dict) -> None:
    """Display programme information. Empty fields are hidden."""
    def filled(value):
        return value is not None and value != ""

    def display(value):
        return str(value) if filled(value) else "-"

    # (label, lines) for fields that have data
    fields = []
    missing = []

    gpa = program.get("minimumGpa")
    scale = program.get("minimumGpaScale")
    if filled(gpa):
        fields.append(("Minimum GPA", [f"{gpa} / {scale}" if scale else str(gpa)]))
    else:
        missing.append("GPA")

    languages = [
        f"{item.get('testType', 'Test')}: {item.get('minimumScore')}"
        for item in (program.get("languageRequirements") or [])
        if filled(item.get("minimumScore"))
    ]
    if languages:
        fields.append(("Language requirements", languages))
    else:
        missing.append("language scores")

    tuition = program.get("tuition")
    amount = tuition.get("amount") if isinstance(tuition, dict) else None
    if isinstance(amount, (int, float)):
        fields.append((
            "Tuition fee",
            [f"{amount:,.0f} {tuition.get('currency', '')} / {tuition.get('period', '')}"],
        ))
    else:
        missing.append("tuition")

    deadline = program.get("applicationDeadline")
    if filled(deadline):
        fields.append(("Application deadline", [str(deadline)]))
    else:
        missing.append("deadline")

    scholarships = [
        item.get("name", "Scholarship")
        for item in (program.get("scholarships") or [])
    ]
    if scholarships:
        fields.append(("Scholarships", scholarships))

    requirement = program.get("academicRequirementText")
    if filled(requirement):
        fields.append(("Academic requirement", [str(requirement)]))

    with st.container(border=True):
        st.subheader(program.get("universityName", "University"))
        st.markdown(f"**{program.get('programName', 'Programme')}**")

        country = COUNTRIES.get(
            program.get("country"), program.get("country", "")
        )
        degree = DEGREES.get(
            program.get("degreeLevel"), program.get("degreeLevel", "")
        )
        meta = [country, degree]
        if filled(program.get("intake")):
            meta.append(f"Intake: {program.get('intake')}")
        st.caption(" · ".join(str(m) for m in meta if m))

        if fields:
            left, right = st.columns(2)
            for index, (label, lines) in enumerate(fields):
                with (left if index % 2 == 0 else right):
                    st.markdown(f"**{label}**")
                    for line in lines:
                        st.write(line)

        if program.get("verificationStatus") == "ai_suggested":
            st.info(
                "Found by Gemini web search. Admission eligibility "
                "has not yet been assessed."
            )
        else:
            st.info(
                "Catalogue match only. Admission eligibility "
                "has not yet been assessed."
            )

        url = str(program.get("sourceUrl") or "")
        if missing:
            note = ", ".join(missing)
            note = note[0].upper() + note[1:]
            if url.startswith("https://"):
                st.caption(f"{note}: please check the [official source]({url}).")
            else:
                st.caption(f"{note}: please check the university's official website.")
        elif url.startswith("https://"):
            st.markdown(f"[Official source]({url})")

        st.caption(
            f"Record status: "
            f"{display(program.get('verificationStatus'))} · "
            f"Checked: {display(program.get('checkedAt'))}"
        )


def submit_search() -> None:
    """Validate stored inputs and save the last successful search."""
    state = st.session_state
    errors = []

    transcript = (state.get("transcript") or "").strip().upper()
    nationality = (state.get("nationality") or "").strip().upper()
    score = state["score"]
    maximum = state["maximum"]

    if transcript not in WORLD_NAMES:
        errors.append("Choose the country that issued your transcript.")

    if score is None:
        errors.append("Enter your academic score.")

    if state["grading"] in ("gpa", "total_score"):
        if maximum is None or maximum <= 0:
            errors.append("Enter a maximum score greater than zero.")
        elif score is not None and score > maximum:
            errors.append("Your score cannot exceed the maximum score.")

    if (
        state["grading"] == "percentage"
        and score is not None
        and score > 100
    ):
        errors.append("A percentage score cannot exceed 100.")

    if state["test"] != "none" and state["test_score"] is None:
        errors.append("Enter a score for your selected language test.")

    if state["test"] == "none" and state["test_score"] is not None:
        errors.append("Select the language test for your score.")

    state["input_errors"] = errors
    state["saved_notice"] = not errors

    if errors:
        return

    state["search"] = {
        "applicantType": state["degree"],
        "currentEducationLevel": state["education"],
        "transcriptCountry": transcript,
        "nationality": nationality or None,
        "academicScore": score,
        "gradingSystem": state["grading"],
        "maximumScore": maximum,
        # Nothing selected = all engineering fields / all five countries (SPEC 3.1, AC16).
        "engineeringFields": list(state["fields"]) or list(FIELDS),
        "interests": (
            (state.get("agent_context") or {}).get("interests")
        ),
        "preferredCountries": list(state["countries"]) or list(COUNTRIES),
        "maximumTuition": state["budget"],
        "tuitionCurrency": state["currency"],
        "tuitionPeriod": state["period"],
        "languageTestType": (
            None if state["test"] == "none" else state["test"]
        ),
        "languageTestScore": state["test_score"],
        "scholarshipRequired": state["scholarship"],
    }


def send_message() -> None:
    """Send a chat message to Intake Agent and update form values."""
    import requests

    state = st.session_state
    message = state.get("chat_draft", "").strip()

    if not message:
        return

    history = state.setdefault("chat_history", [])
    history.append({
        "role": "user",
        "text": message,
    })

    # AC21: answer in the language the user writes in (runs in the Send callback,
    # before the language selector widget is drawn).
    state["ui_language"] = detect_language(
        [item["text"] for item in history if item["role"] == "user"],
        default=state.get("ui_language", "en"),
    )

    try:
        response = requests.post(
            f"{API_BASE_URL}/agent/run",
            json={
                "text": message,
                "previousContext": state.get("agent_context"),
            },
            timeout=(10, 120),
        )
        response.raise_for_status()
        result = response.json()

        state["intake_result"] = result
        context = result.get("context") or {}
        state["agent_context"] = context

        # Match API fields to Streamlit widget keys.
        field_mapping = {
            "applicantType": "degree",
            "currentEducationLevel": "education",
            "transcriptCountry": "transcript",
            "nationality": "nationality",
            "academicScore": "score",
            "gradingSystem": "grading",
            "maximumScore": "maximum",
            "engineeringFields": "fields",
            "preferredCountries": "countries",
            "maximumTuition": "budget",
            "tuitionCurrency": "currency",
            "tuitionPeriod": "period",
            "languageTestType": "test",
            "languageTestScore": "test_score",
            "scholarshipRequired": "scholarship",
        }

        allowed_choices = {
            "degree": set(DEGREES),
            "education": set(EDUCATION),
            "grading": set(GRADING),
            "fields": set(FIELDS),
            "countries": set(COUNTRIES),
            "currency": {"KRW", "USD", "GBP", "EUR"},
            "period": set(PERIODS),
            "test": {
                "none",
                "IELTS",
                "TOEFL_iBT",
                "Duolingo",
                "TOPIK",
                "other",
            },
        }

        numeric_keys = {
            "score",
            "maximum",
            "budget",
            "test_score",
        }

        for api_field, ui_field in field_mapping.items():
            value = context.get(api_field)

            if value is None:
                continue

            if ui_field in ("fields", "countries"):
                if not isinstance(value, list):
                    continue
                value = [
                    item
                    for item in value
                    if item in allowed_choices[ui_field]
                ]

            elif ui_field in allowed_choices:
                if value not in allowed_choices[ui_field]:
                    continue

            elif ui_field in numeric_keys:
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    continue

                if value < 0:
                    continue

            elif ui_field in ("transcript", "nationality"):
                value = str(value).strip().upper()
                if value not in WORLD_NAMES:
                    continue

            state[ui_field] = value

                # Display Root Agent results in the existing chat UI.
        if result.get("stage") == "recommendation":
            recommendation = result.get("recommendation") or {}
            candidates = recommendation.get("candidates") or []
            catalogue = result.get("catalogueMatches") or []

            lines = [
                t("Analysis complete."),
                f"{t('Verified candidates')}: {len(candidates)}",
                f"{t('Matching programmes')}: {len(catalogue)}",
            ]

            if catalogue:
                lines.append("")
                lines.append(t("Matching programmes (admission requirements not yet checked):"))

                for item in catalogue:
                    name = (
                        item.get("program_name")
                        or item.get("programName")
                        or item.get("candidate_id")
                        or t("Name to be confirmed")
                    )
                    university = item.get("universityName")
                    lines.append(
                        f"- {university} · {name}" if university else f"- {name}"
                    )

                lines.append("")
                lines.append(t("See the detailed cards in the Results tab. Check the conditions on the right, then press Search."))

            follow_ups = recommendation.get("followUps") or []

            if follow_ups:
                lines.append("")
                lines.extend(
                    str(item) for item in follow_ups
                )

            assistant_text = "\n".join(lines)

        else:
            follow_ups = result.get("followUps") or []
            questions = []

            for item in follow_ups:
                if isinstance(item, dict):
                    field = item.get("field")
                    question = (
                        t(FOLLOW_UP_QUESTIONS[field])
                        if field in FOLLOW_UP_QUESTIONS
                        else item.get("question")
                    )
                    if question:
                        questions.append(question)
                elif isinstance(item, str):
                    questions.append(item)

            if questions:
                assistant_text = "\n".join(questions)
            else:
                assistant_text = t("More information is needed. Please check the conditions on the right.")

        history.append({
            "role": "assistant",
            "text": assistant_text,
        })

    except requests.RequestException as error:
        history.append({
            "role": "assistant",
            "text": f"{t('Could not reach the server')}: {error}",
        })

    except (ValueError, TypeError, KeyError) as error:
        history.append({
            "role": "assistant",
            "text": f"{t('Could not read the assistant response')}: {error}",
        })

    state["chat_draft"] = ""


def show_conversation() -> None:
    """Show conversation history above a message composer."""
    st.subheader(t("Tell us about your plans"))
    st.caption(t("Describe what you want to study and where."))

    history = st.session_state.setdefault("chat_history", [])

    with st.container(height=470, border=False):
        if not history:
            st.markdown(
                f"""
<div class="chat-empty">
<div class="chat-empty-icon">✦</div>
<h3>{label("Start by telling us about your study plans.")}</h3>
<p>{label("Your messages will appear here.")}</p>
</div>
""",
                unsafe_allow_html=True,
            )

        for message in history:
            is_user = message["role"] == "user"
            speaker = t("You") if is_user else "Global Admission AI"
            bubble_class = (
                "user-bubble" if is_user else "assistant-bubble"
            )
            text = (
                t(message["text"])
                if message.get("translate")
                else message["text"]
            )

            st.markdown(
                f"""
<div class="chat-speaker">{safe(speaker)}</div>
<div class="chat-bubble {bubble_class}">{safe(text)}</div>
""",
                unsafe_allow_html=True,
            )

    with st.form("message_composer", border=True):
        message_column, send_column = st.columns(
            [5, 1],
            vertical_alignment="bottom",
        )

        with message_column:
            st.text_input(
                t("Your message"),
                placeholder=t("Add information or corrections…"),
                label_visibility="collapsed",
                key="chat_draft",
            )

        with send_column:
            st.form_submit_button(
                t("Send"),
                type="primary",
                use_container_width=True,
                on_click=send_message,
            )

    st.caption(
        "Intake Agent가 대화에서 조건을 추출하고 "
        "오른쪽 입력 폼에 자동 반영합니다."
        if st.session_state.get("ui_language") == "ko"
        else (
            "The Intake Agent extracts information from your "
            "messages and updates the form automatically."
        )
    )


def show_input(programs) -> None:
    """Render inputs with stable keys so language switches preserve values."""
    left, right = st.columns([0.9, 1.25], gap="large")

    with left:
        show_conversation()

    with right:
        st.subheader(t("Your conditions"))
        st.caption(
            t("Complete the form to explore the sample catalogue.")
        )

        with st.container(border=True):
            a, b = st.columns(2)

            with a:
                choice("Degree", DEGREES, "degree", "master")

                st.selectbox(
                    t("Country that issued your transcript"),
                    list(WORLD_NAMES),
                    index=None,
                    placeholder=t("Type or choose a country"),
                    format_func=country_name,
                    key="transcript",
                )

                st.number_input(
                    t("Academic score"),
                    min_value=0.0,
                    value=None,
                    step=0.1,
                    key="score",
                )

            with b:
                choice(
                    "Current / highest education",
                    EDUCATION,
                    "education",
                    "bachelor",
                )

                choice(
                    "Grading system",
                    GRADING,
                    "grading",
                    "gpa",
                )

                st.number_input(
                    t("Maximum score, if applicable"),
                    min_value=0.0,
                    value=None,
                    step=0.1,
                    key="maximum",
                )

            if "fields" not in st.session_state:
                st.session_state["fields"] = []

            if "countries" not in st.session_state:
                st.session_state["countries"] = []

            st.multiselect(
                t("Engineering fields"),
                list(FIELDS),
                format_func=lambda value: t(FIELDS[value]),
                key="fields",
                placeholder=t("Leave empty to search all engineering fields."),
            )

            st.caption(
                t("All engineering fields in Korea, the US, the UK, the Netherlands and Ireland.")
            )

            st.multiselect(
                t("Preferred countries"),
                list(COUNTRIES),
                format_func=lambda value: t(COUNTRIES[value]),
                key="countries",
                placeholder=t("Leave empty to search all five countries."),
            )

            a, b = st.columns(2)

            with a:
                st.number_input(
                    t("Maximum tuition — optional"),
                    min_value=0.0,
                    value=None,
                    step=1000.0,
                    key="budget",
                )

                st.selectbox(
                    t("Tuition currency"),
                    ["KRW", "USD", "GBP", "EUR"],
                    key="currency",
                )

                st.selectbox(
                    t("Nationality — optional"),
                    list(WORLD_NAMES),
                    index=None,
                    placeholder=t("Type or choose a country"),
                    format_func=country_name,
                    key="nationality",
                )

            with b:
                choice(
                    "Tuition period",
                    PERIODS,
                    "period",
                    "year",
                )

                tests = {
                    "none": "Not provided",
                    "IELTS": "IELTS",
                    "TOEFL_iBT": "TOEFL_iBT",
                    "Duolingo": "Duolingo",
                    "TOPIK": "TOPIK",
                    "other": "Other",
                }

                choice(
                    "Language test — optional",
                    tests,
                    "test",
                    "none",
                )

                st.number_input(
                    t("Language score — optional"),
                    min_value=0.0,
                    value=None,
                    step=0.5,
                    key="test_score",
                )

            st.checkbox(
                t("I need a scholarship"),
                key="scholarship",
            )

            st.caption(
                t("Advisor matching will be added after the MVP.")
            )

            st.button(
                t("Find sample programmes →"),
                type="primary",
                use_container_width=True,
                on_click=submit_search,
                key="find_programmes",
            )

        for error in st.session_state.get("input_errors", []):
            st.error(t(error))

        if st.session_state.get("saved_notice"):
            st.success(
                t("Conditions saved. Open the Results tab above.")
            )




def show_official_search(program: dict) -> None:
    """Search official admission requirements using Gemini Google Search."""
    import os
    import hashlib
    from urllib.parse import urlparse

    from dotenv import load_dotenv

    uid = hashlib.sha256(
        str(program.get("programId", program)).encode()
    ).hexdigest()[:16]

    state_key = "official_search_" + uid

    if st.button(
        "🔎 Search official admission requirements",
        key="official_btn_" + uid,
    ):
        try:
            load_dotenv(ROOT / ".env")

            from google import genai
            from google.genai import types

            api_key = (
                os.getenv("GEMINI_API_KEY")
                or os.getenv("GOOGLE_API_KEY")
            )
            model = os.getenv(
                "GEMINI_MODEL",
                "gemini-3.8-flash",
            )

            if not api_key:
                raise ValueError("GEMINI_API_KEY is missing.")

            source_url = str(program.get("sourceUrl") or "")
            university = program.get("universityName", "")
            programme = program.get("programName", "")
            degree = program.get("degreeLevel", "")

            host = urlparse(source_url).hostname

            if not source_url.startswith("https://") or not host:
                raise ValueError(
                    "Official university source URL is missing."
                )

            prompt = f"""
You are an international university admissions research assistant.

Search official university websites for the following programme.

University: {university}
Programme: {programme}
Degree: {degree}
Official starting URL: {source_url}

Find and report:

1. Academic requirements
- Minimum GPA if officially published
- Required degree classification
- Country-specific international qualifications
- Do not invent GPA conversions

2. English language requirements
- IELTS overall and minimum component scores
- TOEFL iBT requirements
- PTE or other accepted tests
- Identify the applicable admission year

3. Tuition fees
- Amount
- Currency
- Billing period
- International student tuition where available

4. Scholarships
- Scholarship name
- Eligibility conditions
- Official scholarship URL

5. Application deadlines
- Application year
- Exact deadline where officially published

6. Official verification links
- Include the official university URL supporting each section
- Do not use blogs or unofficial admission websites

IMPORTANT RULES:
- Use official university sources whenever possible.
- Do not fabricate requirements.
- Do not assume that a UK 2:1 degree equals a particular GPA.
- If information cannot be verified, write NOT VERIFIED.
- Distinguish programme-specific requirements from general requirements.
- Do not predict admission probability.
- Respond in Korean.

Use this response format:

## Academic requirements
...

## English language requirements
...

## Tuition fees
...

## Scholarships
...

## Application deadlines
...

## Official sources
...
"""

            with st.spinner(
                "Searching official university admission requirements..."
            ):
                client = genai.Client(api_key=api_key)

                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[
                            types.Tool(
                                google_search=types.GoogleSearch()
                            )
                        ],
                        temperature=0,
                    ),
                )

            sources = []

            if response.candidates:
                metadata = getattr(
                    response.candidates[0],
                    "grounding_metadata",
                    None,
                )

                chunks = (
                    getattr(metadata, "grounding_chunks", None)
                    or []
                )

                for chunk in chunks:
                    web_source = getattr(chunk, "web", None)

                    if web_source:
                        url = getattr(web_source, "uri", None)
                        title = getattr(web_source, "title", None)

                        if url:
                            sources.append({
                                "title": title or "Source",
                                "url": url,
                            })

            st.session_state[state_key] = {
                "text": response.text or "No information returned.",
                "sources": sources,
                "model": model,
            }

        except Exception as error:
            message = str(error)

            if "429" in message or "RESOURCE_EXHAUSTED" in message:
                message = (
                    "Gemini API quota exceeded. "
                    "Please try again later."
                )

            st.session_state[state_key] = {
                "error": message
            }

    result = st.session_state.get(state_key)

    if not result:
        return

    if result.get("error"):
        st.error(result["error"])
        return

    st.markdown("### AI Admission Requirements Research")

    st.caption(
        "Gemini model: " + result.get("model", "")
    )

    st.markdown(result.get("text", ""))

    sources = result.get("sources", [])

    if sources:
        st.markdown("### Search citations")

        seen = set()

        for source in sources:
            url = source["url"]

            if url in seen:
                continue

            seen.add(url)

            st.markdown(
                f"- [{source['title']}]({url})"
            )
    else:
        st.warning(
            "No search citations were returned. "
            "The information is not independently verified."
        )

    st.info(
        "AI-generated research must be checked against "
        "the linked official university pages."
    )

SOURCE_LABELS = {
    "team_verified": "Official admission guide (team checked)",
    "official_dataset": "Government open data",
    "web_verified": "Found by web search",
}
TIER_LABELS = {
    "reach": "Reach",
    "match": "Match",
    "safety": "Safety",
    "unknown": "Difficulty not available",
}
STATUS_LABELS = {
    "met": ("✅", "Met"),
    "unmet": ("❌", "Not met"),
    "needs_check": ("⚠️", "Needs checking"),
}
ITEM_LABELS = {
    "academic": "Grade requirement",
    "language": "Language requirement",
    "tuition": "Tuition vs. budget",
    "deadline": "Application deadline",
}
REASON_LABELS = {
    "minimum_not_published": "minimum not published, check the official guide",
    "scale_not_comparable": "grading scales cannot be compared",
    "different_scale": "different grading scale, check the official conversion",
    "not_recorded": "not recorded yet, check the official guide",
    "no_score_entered": "enter your language test score to compare",
    "test_not_listed": "your test is not listed for this programme",
    "budget": "compared with your maximum tuition",
}
BUDGET_LABELS = {
    "within": "Within your budget",
    "needs_check": "Tuition to be checked",
}


def v2_context(context: dict) -> dict:
    """Search context for recommend_v2: a grade tier only when the score has a numeric scale."""
    ctx = dict(context)
    grading = context.get("gradingSystem")
    if grading == "percentage":
        ctx["maximumScore"] = 100
    elif grading not in ("gpa", "total_score"):
        ctx["academicScore"] = None
    return ctx


def show_recommendation_card(program: dict) -> None:
    """Result card: what the applicant needs, with official links (SPEC F02, F08, AC24, AC25, AC27)."""
    english = st.session_state.get("ui_language") != "ko"
    university = (program.get("universityNameEnglish") if english else None) or program.get("universityName")
    with st.container(border=True):
        st.markdown(f"### {safe(university)}")
        country = t(COUNTRIES.get(program.get("country"), program.get("country") or ""))
        degree = t({"undergraduate": "Undergraduate", "master": "Master", "phd": "PhD"}.get(program.get("degreeLevel"), ""))
        badges = []
        if program.get("admissionTier"):
            badges.append(t(TIER_LABELS[program["admissionTier"]]))
        if program.get("budgetFit") == "within":
            badges.append(t("Within your budget"))
        st.markdown(
            f"**{safe(program.get('programName'))}** · {country} · {degree}"
            + ("  " + " ".join(f"`{b}`" for b in badges) if badges else "")
        )

        tuition = program.get("tuition") or {}
        if tuition.get("amount"):
            st.write(f"💰 {t('Tuition')}: {tuition['amount']:,.0f} {tuition.get('currency', '')} / {t(tuition.get('period', 'year'))}")

        if program.get("academicRequirementText") and program.get("source") == "official_dataset":
            with st.expander(t("Admission details from the official guide")):
                show_card(program)

        sources = program.get("requirementSources") or {}
        program_page = program.get("programPageUrl") or next(iter(sources.values()), None)
        if not program_page and program.get("source") in ("team_verified", "web_verified"):
            program_page = program.get("sourceUrl")
        st.caption(t("Check the details on the official page below."))
        links = []
        if program_page:
            links.append(f"[📄 **{t('Official programme page')}**]({program_page})")
        elif program.get("officialDomain"):
            links.append(f"[🏛 {t('University website')}](https://{program['officialDomain']})")
        if program.get("sourceUrl") and program.get("sourceUrl") != program_page:
            links.append(f"[📊 {t(SOURCE_LABELS.get(program.get('source'), 'Data source'))}]({program['sourceUrl']})")
        st.markdown(" · ".join(links))
        if program.get("difficultyPercentile") is not None:
            st.caption(f"{t('Difficulty index')} {program['difficultyPercentile']:.0f}/100 · {t(program.get('difficultyBasis') or '')}")


def enrich_with_requirements(results: list[dict], ctx: dict) -> list[dict]:
    """Look up each result's requirements on its official site, in parallel, cached per programme."""
    from concurrent.futures import ThreadPoolExecutor

    cache = st.session_state.setdefault("requirement_cache", {})

    def domain_for(p):
        return p.get("officialDomain") or next(iter(official_domains(p.get("universityNameEnglish") or p["universityName"], p.get("country"))), None)

    todo = [p for p in results if p["programId"] not in cache]
    if todo:
        def work(p):
            try:
                domain = domain_for(p)
                return p["programId"], domain, find_requirements(p, ctx, domain)
            except Exception:
                return p["programId"], None, {"sources": {}}
        with st.spinner(t("Loading programme information...")):
            with ThreadPoolExecutor(max_workers=5) as pool:
                for pid, domain, found in pool.map(work, todo):
                    cache[pid] = {"domain": domain, "found": found}

    enriched = []
    for p in results:
        entry = cache.get(p["programId"], {"found": {"sources": {}}})
        found = entry["found"]
        merged = {**p, **{k: v for k, v in found.items() if k != "sources" and not p.get(k)}}
        merged["requirementSources"] = found.get("sources") or {}
        if not merged.get("officialDomain") and entry.get("domain"):
            merged["officialDomain"] = entry["domain"]
        merged["requirements"] = requirement_status(merged, ctx)
        enriched.append(merged)
    return enriched


@st.cache_data(show_spinner=False)
def gemini_fill(context_json: str, exclude: tuple) -> list[dict]:
    """Ask Gemini for more programmes, then keep only links that open on the university's domain."""
    context = json.loads(context_json)
    raw = explore_programmes(context, set(exclude))
    return web_results_from_gemini(raw, context)


def show_scholarships(context: dict, results: list[dict]) -> None:
    """Government scholarships for the chosen countries; university scholarships link out (F09, AC26)."""
    info = scholarships_for(context)
    st.subheader(t("International scholarships"))
    st.caption(t("Shown with their conditions. Being listed here does not mean you are eligible."))

    if not info["national"]:
        st.info(t("No government scholarship in our data for this country and degree."))
    for item in info["national"]:
        with st.container(border=True):
            st.markdown(f"**{safe(item['name'])}** · {t(COUNTRIES.get(item['country'], item['country']))}")
            if item.get("provider"):
                st.caption(item["provider"])
            for line in item["conditions"][:4]:
                st.write("• " + line)
            if item["benefits"]:
                st.write(t("Benefits") + ": " + "; ".join(item["benefits"][:3]))
            note = item.get("nationalityNote")
            if note == "listed_for_myanmar":
                st.success(t("Myanmar is listed for this scholarship. Check the current call before applying."))
            elif note == "check_country_list":
                st.warning(t("Check whether your country is on this scholarship's country list."))
            if item.get("sourceUrl"):
                st.markdown(f"[📄 {t('Official scholarship page')}]({item['sourceUrl']})")
            if item.get("verificationStatus") != "verified":
                st.caption(t("Collected from the official page; team review pending."))

    sites = []
    for program in results:
        domain = program.get("officialDomain")
        if domain and domain not in [d for d, _ in sites]:
            sites.append((domain, program.get("universityNameEnglish") or program.get("universityName")))
    st.markdown("**" + t("University scholarships") + "**")
    st.write(t("University scholarships depend on your grades and change every intake, so they are not judged here. Check each university's official page."))
    if sites:
        st.markdown(" · ".join(f"[{safe(name)}](https://{domain})" for domain, name in sites))


def show_results(programs: list[dict] | None = None) -> None:
    """Five distinct universities ranked by grade tier and budget (SPEC F06, F08)."""
    context = st.session_state.get("search")
    if not context:
        st.info(t("Enter your conditions and search first."))
        return

    ctx = v2_context(context)
    catalogue = load_unified_catalogue()
    outcome = recommend_v2(ctx, catalogue)

    if outcome["shortfallReason"]:
        exclude = tuple(sorted(str(p.get("universityName", "")).lower() for p in outcome["results"]))
        try:
            with st.spinner(t("Searching official university websites for more programmes...")):
                web = gemini_fill(json.dumps(context, sort_keys=True, default=str), exclude)
            outcome = recommend_v2(ctx, catalogue, web_results=web)
        except Exception as error:  # web search is optional; dataset results still stand
            message = str(error)
            if "429" in message or "RESOURCE_EXHAUSTED" in message:
                message = t("Gemini API quota exceeded. Please try again later.")
            st.caption(f"{t('Web search unavailable')}: {message}")

    results = enrich_with_requirements(outcome["results"], ctx)
    st.subheader(f"{t('Recommended universities')} · {len(results)}")
    st.caption(
        t("Ranked by your grade and budget using public indicators. "
          "Tiers are estimates, not admission predictions. Check requirements on each official source.")
    )
    if outcome["shortfallReason"]:
        st.info(t("Fewer than five universities meet every condition. Conditions were not relaxed."))

    for program in results:
        show_recommendation_card(program)

    show_scholarships(context, results)



def enter_guest_mode() -> None:
    """Open the sample app without authenticating an account."""
    st.session_state["guest_access"] = True


def return_to_login():
    language = st.session_state.get("ui_language", "en")
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state["ui_language"] = language




def login_user(email, password):
    import requests

    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={
                "email": email.strip(),
                "password": password,
            },
            timeout=45,
        )

        if response.status_code != 200:
            return {
                "error": (
                    f"{t('Sign-in failed')}: HTTP {response.status_code} "
                    f"- {response.text}"
                )
            }

        data = response.json()

        if not data.get("access_token"):
            return {
                "error": t("The server did not return a sign-in token.")
            }

        return data

    except requests.Timeout:
        return {
            "error": t("The server took too long to respond. Please try again shortly.")
        }

    except requests.RequestException as error:
        return {
            "error": f"{t('Could not reach the server')}: {type(error).__name__}"
        }




def show_login():
    st.title(t("Welcome to Global Admission AI"))
    st.write(t("Find your next engineering programme."))

    left, right = st.columns([1.15, 1], gap="large")

    with left:
        with st.container(border=True):
            st.subheader("🌍 Compare programmes")
            st.write("Explore engineering programmes across five countries.")
        with st.container(border=True):
            st.subheader("🔗 Check official sources")
            st.write("Find university admission requirements.")
        with st.container(border=True):
            st.subheader("📋 Know what to prepare")
            st.write("Compare your academic and language qualifications.")

    with right:
        with st.container(border=True):
            mode = st.radio(
                "Account",
                ["Sign in", "Create account"],
                horizontal=True,
            )

            with st.form("authentication_form"):
                email = st.text_input("Email address")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button(
                    "Sign in" if mode == "Sign in" else "Create account",
                    type="primary",
                    use_container_width=True,
                )

            if submitted:
                if not email.strip() or not password:
                    st.error(t("Please enter your email and password."))
                elif mode == "Create account":
                    result = register_user(email, password)
                    if result.get("error"):
                        st.error(result["error"])
                    else:
                        st.success(t("Account created. Choose Sign in to log in."))
                else:
                    result = login_user(email, password)
                    if result.get("error"):
                        st.error(result["error"])
                    else:
                        token = result["access_token"]
                        user = get_current_user(token)
                        if user.get("error"):
                            st.error(user["error"])
                        else:
                            st.session_state["auth_token"] = token
                            st.session_state["auth_user"] = user
                            st.session_state["guest_access"] = False
                            st.rerun()




def main() -> None:
    """Render the bilingual application."""
    st.set_page_config(
        page_title="Global Admission AI",
        page_icon="🎓",
        layout="wide",
    )

    st.markdown(CSS, unsafe_allow_html=True)

    brand, language = st.columns([4, 1])

    with brand:
        st.markdown(
            '<div class="topbar"><div class="logo"></div>'
            "Global Admission AI</div>",
            unsafe_allow_html=True,
        )

    with language:
        st.selectbox(
            "Language / 언어",
            ["en", "ko"],
            format_func=lambda value: {
                "en": "English",
                "ko": "한국어",
            }[value],
            key="ui_language",
        )

        st.caption("BridgeU · " + t("Sample preview"))

    is_guest = False
    is_logged_in = bool(st.session_state.get("auth_token"))

    if not is_guest and not is_logged_in:
        show_login()
        return

    st.button(
        "Log out",
        on_click=return_to_login,
        key="back_to_login",
    )

    try:
        programs = load_programs()

    except (FileNotFoundError, sqlite3.Error, ValueError) as error:
        st.error(
            t("Unable to load the sample database.")
        )
        st.code(str(error))
        st.stop()

    st.caption(
        "2027 모집 여부와 상세 요건이 아직 확인되지 않은 "
        "과정도 포함됩니다. 각 과정의 출처와 확인 필요 항목을 확인하세요."
        if st.session_state.get("ui_language") == "ko"
        else (
            "Some catalogue entries do not yet have confirmed "
            "2027 intake requirements. Check each programme's "
            "sources and unresolved items."
        )
    )

    with st.expander(t("Catalogue coverage")):
        st.write(
            f'{len({p["universityName"] for p in programs})} '
            + t("universities")
            + f' · {len(programs)} '
            + t("programmes")
        )

        st.caption(
            t(
                "Every listed university has undergraduate, "
                "master and doctoral entries. "
                "Detailed admissions remain subject to checking."
            )
        )

        for code, country in COUNTRIES.items():
            schools = sorted({
                p["universityName"]
                for p in programs
                if p["country"] == code
            })

            st.write(
                "**"
                + t(country)
                + "** · "
                + " / ".join(schools)
            )

    input_tab, results_tab = st.tabs(
        [
            "① " + t("Enter conditions"),
            "② " + t("Results"),
        ]
    )

    with input_tab:
        show_input(programs)

    with results_tab:
        show_results(programs)




def register_user(email, password):
    import requests

    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json={
                "email": email.strip(),
                "password": password,
            },
            timeout=15,
        )

        if response.status_code == 201:
            return response.json()

        if response.status_code == 409:
            return {"error": t("This email is already registered.")}

        if response.status_code == 422:
            return {
                "error": t("Enter a valid email and a password of at least 8 characters.")
            }

        return {
            "error": t("Sign-up failed") + ": HTTP " + str(response.status_code)
        }

    except requests.RequestException:
        return {
            "error": t("Could not reach the server")
        }


def get_current_user(token):
    import requests

    try:
        response = requests.get(
            f"{API_BASE_URL}/auth/me",
            headers={
                "Authorization": "Bearer " + token
            },
            timeout=15,
        )

        if response.status_code == 200:
            return response.json()

        return {
            "error": t("Your session has expired. Please sign in again.")
        }

    except requests.RequestException:
        return {
            "error": "사용자 정보를 확인할 수 없습니다."
        }


if __name__ == "__main__":
    main()
