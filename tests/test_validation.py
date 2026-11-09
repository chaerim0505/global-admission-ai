import pytest
from fastapi.testclient import TestClient

from admission.main import app


client = TestClient(app)


@pytest.fixture
def valid_input():
    return {
        "applicantType": "master",
        "currentEducationLevel": "bachelor",
        "transcriptCountry": "MM",
        "academicScore": 3.4,
        "gradingSystem": "gpa",
        "maximumScore": 4.0,
        "engineeringFields": ["computing"],
        "interests": ["AI"],
        "preferredCountries": ["IE", "NL"],
        "maximumTuition": 20000,
        "tuitionCurrency": "EUR",
        "tuitionPeriod": "year",
    }


def test_empty_input():
    response = client.post("/validate", json={})

    assert response.status_code == 422

    errors = response.json()["inputErrors"]
    assert len(errors) == 6
    assert {error["field"] for error in errors} == {
        "applicantType",
        "currentEducationLevel",
        "transcriptCountry",
        "academicScore",
        "gradingSystem",
        "interests",
    }
    assert all(error["problem"] == "missing" for error in errors)


def test_valid_input(valid_input):
    response = client.post("/validate", json=valid_input)

    assert response.status_code == 200

    body = response.json()
    assert body["valid"] is True

    for field, value in valid_input.items():
        assert body["context"][field] == value

    # Missing nationality must not be inferred from transcriptCountry.
    assert body["context"]["nationality"] is None


def test_score_above_maximum(valid_input):
    valid_input["academicScore"] = 4.5

    response = client.post("/validate", json=valid_input)

    assert response.status_code == 422

    errors = response.json()["inputErrors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "academicScore"
    assert errors[0]["problem"] == "out_of_range"


def test_tuition_missing_units(valid_input):
    valid_input["tuitionCurrency"] = None
    valid_input["tuitionPeriod"] = None

    response = client.post("/validate", json=valid_input)

    assert response.status_code == 422

    errors = response.json()["inputErrors"]
    assert len(errors) == 2
    assert {error["field"] for error in errors} == {
        "tuitionCurrency",
        "tuitionPeriod",
    }
    assert all(
        error["problem"] == "missing_dependency"
        for error in errors
    )