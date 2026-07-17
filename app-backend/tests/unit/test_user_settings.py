"""Unit tests for JWT-backed /user-settings routes."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.exceptions import register_exception_handlers
from app.middleware.auth import get_current_user
from app.routers import user_settings

AUTH_USER_ID = "550e8400-e29b-41d4-a716-446655440000"
OTHER_USER_ID = "550e8400-e29b-41d4-a716-446655440099"

SETTINGS_ROW = {
    "id": "550e8400-e29b-41d4-a716-446655440070",
    "user_id": AUTH_USER_ID,
    "allow_trusted_contacts": True,
    "allow_mychart_integration": False,
    "enable_reminders": True,
    "updated_at": datetime(2026, 6, 8, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
}


def _fake_user():
    return {"id": AUTH_USER_ID, "email": "patient@example.com"}


def _build_app(*, authed: bool = True) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(user_settings.router)
    if authed:
        app.dependency_overrides[get_current_user] = _fake_user
    return app


def _table_chain(data):
    """Build a fluent Supabase table mock that ends in execute().data = data."""
    result = MagicMock()
    result.data = data
    chain = MagicMock()
    chain.select.return_value = chain
    chain.insert.return_value = chain
    chain.update.return_value = chain
    chain.eq.return_value = chain
    chain.execute.return_value = result
    return chain


def test_get_settings_requires_auth():
    client = TestClient(_build_app(authed=False), raise_server_exceptions=False)
    resp = client.get("/user-settings/")
    assert resp.status_code == 401
    body = resp.json()
    assert body["success"] is False
    assert body["error_code"] == "UNAUTHORIZED"


def test_get_settings_uses_authenticated_user_id():
    select_chain = _table_chain([SETTINGS_ROW])
    db = MagicMock()
    db.table.return_value = select_chain

    app = _build_app()
    client = TestClient(app, raise_server_exceptions=False)

    with patch("app.routers.user_settings.get_supabase", return_value=db):
        resp = client.get("/user-settings/")

    assert resp.status_code == 200
    assert resp.json()["user_id"] == AUTH_USER_ID
    db.table.assert_called_with("user_settings")
    select_chain.eq.assert_called_with("user_id", AUTH_USER_ID)


def test_get_settings_creates_defaults_when_absent():
    select_chain = _table_chain([])
    insert_chain = _table_chain([SETTINGS_ROW])
    db = MagicMock()
    db.table.side_effect = [select_chain, insert_chain]

    app = _build_app()
    client = TestClient(app, raise_server_exceptions=False)

    with patch("app.routers.user_settings.get_supabase", return_value=db):
        resp = client.get("/user-settings/")

    assert resp.status_code == 200
    assert resp.json()["user_id"] == AUTH_USER_ID
    insert_chain.insert.assert_called_once_with({"user_id": AUTH_USER_ID})


def test_get_settings_ignores_caller_supplied_user_id_query():
    select_chain = _table_chain([SETTINGS_ROW])
    db = MagicMock()
    db.table.return_value = select_chain

    app = _build_app()
    client = TestClient(app, raise_server_exceptions=False)

    with patch("app.routers.user_settings.get_supabase", return_value=db):
        resp = client.get(f"/user-settings/?user_id={OTHER_USER_ID}")

    assert resp.status_code == 200
    assert resp.json()["user_id"] == AUTH_USER_ID
    select_chain.eq.assert_called_with("user_id", AUTH_USER_ID)
    assert OTHER_USER_ID not in [c.args[1] for c in select_chain.eq.call_args_list]


def test_patch_settings_requires_auth():
    client = TestClient(_build_app(authed=False), raise_server_exceptions=False)
    resp = client.patch(
        "/user-settings/",
        json={"enable_reminders": False},
    )
    assert resp.status_code == 401


def test_patch_settings_updates_authenticated_user_only():
    updated = {**SETTINGS_ROW, "enable_reminders": False}
    update_chain = _table_chain([updated])
    db = MagicMock()
    db.table.return_value = update_chain

    app = _build_app()
    client = TestClient(app, raise_server_exceptions=False)

    with patch("app.routers.user_settings.get_supabase", return_value=db):
        resp = client.patch(
            "/user-settings/",
            json={"enable_reminders": False},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == AUTH_USER_ID
    assert body["enable_reminders"] is False
    update_chain.update.assert_called_once_with({"enable_reminders": False})
    update_chain.eq.assert_called_with("user_id", AUTH_USER_ID)


def test_patch_settings_ignores_caller_supplied_user_id_query():
    updated = {**SETTINGS_ROW, "allow_trusted_contacts": False}
    update_chain = _table_chain([updated])
    db = MagicMock()
    db.table.return_value = update_chain

    app = _build_app()
    client = TestClient(app, raise_server_exceptions=False)

    with patch("app.routers.user_settings.get_supabase", return_value=db):
        resp = client.patch(
            f"/user-settings/?user_id={OTHER_USER_ID}",
            json={"allow_trusted_contacts": False},
        )

    assert resp.status_code == 200
    assert resp.json()["user_id"] == AUTH_USER_ID
    update_chain.eq.assert_called_with("user_id", AUTH_USER_ID)
    assert OTHER_USER_ID not in [c.args[1] for c in update_chain.eq.call_args_list]


def test_patch_settings_empty_body_returns_400():
    app = _build_app()
    client = TestClient(app, raise_server_exceptions=False)

    with patch("app.routers.user_settings.get_supabase") as mock_db:
        resp = client.patch("/user-settings/", json={})

    assert resp.status_code == 400
    body = resp.json()
    assert body["success"] is False
    assert "No fields" in body["message"]
    mock_db.assert_not_called()
