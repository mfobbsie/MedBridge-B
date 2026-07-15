"""
Security tests for the patient profile API.

Requires a running FastAPI server and Supabase test credentials.
Start server: uvicorn app.main:app --reload

Run: pytest tests/security/test_patient_profile.py -v
"""

import httpx
import pytest

from tests.security.conftest import USER_A, USER_B, auth_headers, login

PROFILE_URL = "/patient-profile"

VALID_PROFILE = {
    "full_name": "Test Patient",
    "preferred_language": "en",
    "explanation_level": "plain",
}


class TestPatientProfileAuthentication:
    def test_get_rejects_no_token(self, client: httpx.Client):
        resp = client.get(PROFILE_URL)
        assert resp.status_code == 401

    def test_post_rejects_no_token(self, client: httpx.Client):
        resp = client.post(PROFILE_URL, json=VALID_PROFILE)
        assert resp.status_code == 401

    def test_patch_rejects_no_token(self, client: httpx.Client):
        resp = client.patch(PROFILE_URL, json={"full_name": "Updated Name"})
        assert resp.status_code == 401

    def test_get_rejects_bad_token(self, client: httpx.Client):
        resp = client.get(PROFILE_URL, headers={"Authorization": "Bearer not-a-real-token"})
        assert resp.status_code == 401


class TestPatientProfileValidation:
    def test_post_missing_required_fields_returns_422(self, client: httpx.Client):
        token = login(client, USER_A)
        resp = client.post(PROFILE_URL, json={}, headers=auth_headers(token))
        assert resp.status_code == 422

    def test_patch_with_no_fields_returns_400(self, client: httpx.Client):
        token = login(client, USER_A)
        resp = client.patch(PROFILE_URL, json={}, headers=auth_headers(token))
        assert resp.status_code == 400


def _ensure_profile(client: httpx.Client, token: str, full_name: str, preferred_language: str) -> None:
    """Create or complete a profile via POST (handles stub rows and missing rows)."""
    payload = {
        "full_name": full_name,
        "preferred_language": preferred_language,
        "explanation_level": "plain",
    }
    resp = client.post(PROFILE_URL, json=payload, headers=auth_headers(token))
    if resp.status_code == 409:
        resp = client.patch(PROFILE_URL, json=payload, headers=auth_headers(token))
    assert resp.status_code in (200, 201), resp.text


class TestPatientProfileOwnership:
    @pytest.fixture(scope="class", autouse=True)
    def setup_profiles(self, request, client):
        request.cls.token_a = login(client, USER_A)
        request.cls.token_b = login(client, USER_B)

        _ensure_profile(client, request.cls.token_a, "User A Profile", "en")
        _ensure_profile(client, request.cls.token_b, "User B Profile", "es")

    def test_user_a_gets_own_profile(self, client: httpx.Client):
        resp = client.get(PROFILE_URL, headers=auth_headers(self.token_a))
        assert resp.status_code == 200
        data = resp.json()
        assert data["full_name"] == "User A Profile"
        assert data["preferred_language"] == "en"
        assert data["email"] == USER_A["email"]

    def test_user_b_gets_own_profile_not_user_a(self, client: httpx.Client):
        resp = client.get(PROFILE_URL, headers=auth_headers(self.token_b))
        assert resp.status_code == 200
        data = resp.json()
        assert data["full_name"] == "User B Profile"
        assert data["full_name"] != "User A Profile"
        assert data["email"] == USER_B["email"]

    def test_user_a_patch_does_not_change_user_b_profile(self, client: httpx.Client):
        resp = client.patch(
            PROFILE_URL,
            json={"full_name": "User A Updated"},
            headers=auth_headers(self.token_a),
        )
        assert resp.status_code == 200

        resp_b = client.get(PROFILE_URL, headers=auth_headers(self.token_b))
        assert resp_b.json()["full_name"] == "User B Profile"

    def test_post_returns_409_when_profile_already_exists(self, client: httpx.Client):
        resp = client.post(
            PROFILE_URL,
            json=VALID_PROFILE,
            headers=auth_headers(self.token_a),
        )
        assert resp.status_code == 409
