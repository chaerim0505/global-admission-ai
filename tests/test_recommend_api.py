import pytest

pytest.importorskip("fastapi")
pytest.importorskip("google.genai")

from fastapi.testclient import TestClient  # noqa: E402

from admission.main import app  # noqa: E402


client = TestClient(app)


def test_recommend_missing_input_returns_422():
    response = client.post("/recommend", json={"applicantType": "master"})
    assert response.status_code == 422
    assert response.json()["inputErrors"]


def test_recommend_returns_spec_shape():
    response = client.post("/recommend", json={
        "applicantType": "master",
        "currentEducationLevel": "bachelor",
        "transcriptCountry": "MM",
        "academicScore": 3.4,
        "gradingSystem": "gpa",
        "maximumScore": 4.0,
        "engineeringFields": ["computing"],
        "preferredCountries": ["IE"],
    })
    assert response.status_code == 200
    body = response.json()
    assert set(body) >= {"candidates", "excluded", "scopeNotices", "followUps"}
