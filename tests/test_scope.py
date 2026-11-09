from admission.schemas import RequestContext
from admission.scope import check_scope


def test_supported_countries():
    context = RequestContext(preferredCountries=["IE", "NL"])
    assert check_scope(context) == []


def test_unsupported_country():
    context = RequestContext(preferredCountries=["CA"])
    notices = check_scope(context)

    assert notices
    assert "CA" in notices[0]
    assert context.preferredCountries == ["CA"]


def test_nationality_and_transcript_are_not_restricted():
    context = RequestContext(
        preferredCountries=["IE"],
        nationality="MM",
        transcriptCountry="MM",
    )
    assert check_scope(context) == []


def test_unspecified_countries():
    assert check_scope(RequestContext()) == []


def test_mixed_countries_require_confirmation():
    context = RequestContext(preferredCountries=["IE", "CA"])
    assert check_scope(context)


def test_out_of_scope_request():
    context = RequestContext(
        outOfScopeRequests=["MBA 과정 추천"],
    )
    assert check_scope(context)