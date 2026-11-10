from admission.agents import intake_agent
from admission.agents.intake_agent import country_code, run_intake_agent
from admission.schemas import RequestContext


PREVIOUS = RequestContext(
    applicantType="master",
    currentEducationLevel="bachelor",
    academicScore=4.0,
    gradingSystem="gpa",
    maximumScore=4.5,
    engineeringFields=["electrical_electronic"],
)


def test_country_code_accepts_codes_and_names():
    assert country_code("KR") == "KR"
    assert country_code("kr") == "KR"
    assert country_code("Korea") == "KR"
    assert country_code("한국이요") == "KR"
    assert country_code("대한민국입니다.") == "KR"
    assert country_code("미얀마") == "MM"


def test_country_code_covers_all_five_supported_countries():
    answers = {
        "KR": ["KR", "South Korea", "대한민국"],
        "US": ["US", "U.S.A.", "United States", "America", "미국이요"],
        "GB": ["GB", "UK", "U.K.", "United Kingdom", "England", "영국입니다"],
        "NL": ["NL", "Netherlands", "the Netherlands", "Holland", "네덜란드"],
        "IE": ["IE", "Ireland", "아일랜드요"],
    }
    for code, values in answers.items():
        for value in values:
            assert country_code(value) == code, value


def test_country_code_ignores_full_sentences():
    assert country_code("I studied in Korea") is None


def test_bare_country_answer_fills_transcript_country(monkeypatch):
    seen = {}

    def fake_parse(text, pending_questions=None):
        seen["questions"] = pending_questions
        # Simulate the model putting the answer in the wrong field.
        return RequestContext(preferredCountries=["KR"])

    monkeypatch.setattr(intake_agent, "parse_query", fake_parse)

    result = run_intake_agent("KR", PREVIOUS)

    assert seen["questions"] == ["성적표를 발급한 국가는 어디인가요?"]
    assert result["context"]["transcriptCountry"] == "KR"
    assert result["context"]["preferredCountries"] is None
    assert result["readyForRecommendation"] is True


def test_model_answer_is_kept_when_it_already_filled_the_field(monkeypatch):
    monkeypatch.setattr(
        intake_agent,
        "parse_query",
        lambda text, pending_questions=None: RequestContext(
            transcriptCountry="MM", preferredCountries=["KR"]
        ),
    )

    result = run_intake_agent("미얀마에서 졸업했고 한국에 가고 싶어요", PREVIOUS)

    assert result["context"]["transcriptCountry"] == "MM"
    assert result["context"]["preferredCountries"] == ["KR"]
