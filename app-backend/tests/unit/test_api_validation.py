"""Unit tests for request validation behavior on API routes."""

from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.exceptions import register_exception_handlers
from app.middleware.auth import get_current_user
from app.schemas.documents import ChatRequest
from app.schemas.features import ReminderUpdate
from app.utils.validation import UuidStr


def _fake_user():
    return {"id": "550e8400-e29b-41d4-a716-446655440000", "email": "test@example.com"}


def _build_test_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/items/{item_id}")
    async def get_item(item_id: UuidStr, user: dict = Depends(get_current_user)):
        return {"id": item_id, "user_id": user["id"]}

    @app.post("/chat")
    async def chat(payload: ChatRequest, user: dict = Depends(get_current_user)):
        return {"question": payload.question}

    @app.patch("/reminders/{reminder_id}")
    async def patch_reminder(
        reminder_id: UuidStr,
        payload: ReminderUpdate,
        user: dict = Depends(get_current_user),
    ):
        updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
        if not updates:
            raise HTTPException(status_code=400, detail="No fields provided to update.")
        return {"id": reminder_id, **updates}

    class TypedPayload(BaseModel):
        rating: int

    @app.post("/typed")
    async def typed(payload: TypedPayload):
        return payload

    return app


client = TestClient(_build_test_app(), raise_server_exceptions=False)
app = _build_test_app()
app.dependency_overrides[get_current_user] = _fake_user
authed = TestClient(app, raise_server_exceptions=False)


def test_invalid_uuid_path_returns_422():
    resp = authed.get("/items/not-a-uuid")
    assert resp.status_code == 422
    body = resp.json()
    assert body["success"] is False
    assert body["error_code"] == "VALIDATION_ERROR"
    assert body["details"]


def test_valid_uuid_path_succeeds():
    resp = authed.get("/items/550e8400-e29b-41d4-a716-446655440000")
    assert resp.status_code == 200
    assert resp.json()["id"] == "550e8400-e29b-41d4-a716-446655440000"


def test_unauthenticated_returns_401_envelope():
    resp = client.get("/items/550e8400-e29b-41d4-a716-446655440000")
    assert resp.status_code == 401
    body = resp.json()
    assert body["success"] is False
    assert body["error_code"] == "UNAUTHORIZED"


def test_whitespace_question_returns_422():
    resp = authed.post("/chat", json={"question": "   "})
    assert resp.status_code == 422
    body = resp.json()
    assert body["error_code"] == "VALIDATION_ERROR"


def test_wrong_type_returns_422():
    resp = authed.post("/typed", json={"rating": "five"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["error_code"] == "VALIDATION_ERROR"


def test_empty_patch_returns_400():
    resp = authed.patch(
        "/reminders/550e8400-e29b-41d4-a716-446655440001",
        json={},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["success"] is False
    assert body["error_code"] == "BAD_REQUEST"
    assert "No fields" in body["message"]
