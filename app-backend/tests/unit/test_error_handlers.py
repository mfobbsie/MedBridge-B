"""Unit tests for global API error handlers."""

from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.exceptions import MedBridgeHTTPException, register_exception_handlers
from app.middleware.auth import get_current_user
from app.schemas.errors import GENERIC_INTERNAL_ERROR_MESSAGE


def _build_test_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    class SamplePayload(BaseModel):
        password: str = Field(min_length=8)

    @app.get("/not-found")
    async def not_found():
        raise HTTPException(status_code=404, detail="Document not found.")

    @app.get("/protected")
    async def protected(user: dict = Depends(get_current_user)):
        return {"user_id": user["id"]}

    @app.post("/validate")
    async def validate(payload: SamplePayload):
        return {"ok": True}

    @app.get("/boom")
    async def boom():
        raise RuntimeError("secret database password leaked")

    @app.get("/service-unavailable")
    async def service_unavailable():
        raise MedBridgeHTTPException(
            status_code=503,
            detail="The AI is taking longer than usual. Please try again in a moment.",
            error_code="GROQ_TIMEOUT",
            retry_after=5,
        )

    return app


client = TestClient(_build_test_app(), raise_server_exceptions=False)


def test_http_exception_returns_standard_envelope():
    resp = client.get("/not-found")
    assert resp.status_code == 404
    body = resp.json()
    assert body == {
        "success": False,
        "error_code": "NOT_FOUND",
        "message": "Document not found.",
        "details": None,
        "retry_after": None,
    }


def test_unauthorized_returns_standard_envelope():
    resp = client.get("/protected")
    assert resp.status_code == 401
    body = resp.json()
    assert body["success"] is False
    assert body["error_code"] == "UNAUTHORIZED"
    assert body["message"]
    assert body["details"] is None


def test_validation_error_returns_structured_details():
    resp = client.post("/validate", json={"password": "short"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["success"] is False
    assert body["error_code"] == "VALIDATION_ERROR"
    assert body["message"] == "Request validation failed"
    assert len(body["details"]) == 1
    assert body["details"][0]["field"] == "password"
    assert "at least 8 characters" in body["details"][0]["message"]
    assert body["details"][0]["type"] == "string_too_short"


def test_unhandled_exception_hides_internal_details():
    resp = client.get("/boom")
    assert resp.status_code == 500
    body = resp.json()
    assert body["success"] is False
    assert body["error_code"] == "INTERNAL_ERROR"
    assert body["message"] == GENERIC_INTERNAL_ERROR_MESSAGE
    assert "secret database password" not in resp.text


def test_medbridge_http_exception_includes_retry_after():
    resp = client.get("/service-unavailable")
    assert resp.status_code == 503
    body = resp.json()
    assert body == {
        "success": False,
        "error_code": "GROQ_TIMEOUT",
        "message": "The AI is taking longer than usual. Please try again in a moment.",
        "details": None,
        "retry_after": 5,
    }
