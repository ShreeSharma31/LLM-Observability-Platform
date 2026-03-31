from fastapi.testclient import TestClient

import api
from api import app
from database import SessionLocal
from models import LLMLog


client = TestClient(app)


def _clear_logs():
    db = SessionLocal()
    try:
        db.query(LLMLog).delete()
        db.commit()
    finally:
        db.close()


def test_track_and_analytics_roundtrip():
    _clear_logs()
    payload = {
        "user": "alice",
        "model": "gpt-4",
        "cost": 0.0123,
        "latency": 320.5,
        "feature": "chat",
        "environment": "prod",
    }
    track_resp = client.post("/track", json=payload)
    assert track_resp.status_code == 200
    body = track_resp.json()
    assert body["message"] == "Log stored successfully"

    analytics_resp = client.get("/analytics")
    assert analytics_resp.status_code == 200
    data = analytics_resp.json()
    assert data["total_cost"] >= 0.0123
    assert "cost_by_model" in data
    assert "timeseries" in data


def test_track_rejects_negative_values():
    _clear_logs()
    bad_payload = {
        "user": "alice",
        "model": "gpt-4",
        "cost": -1,
        "latency": 200,
        "feature": "chat",
        "environment": "prod",
    }
    resp = client.post("/track", json=bad_payload)
    assert resp.status_code == 400


def test_jwt_token_issue_and_me_endpoint():
    original = api.settings.jwt_auth_enabled
    object.__setattr__(api.settings, "jwt_auth_enabled", True)
    try:
        token_resp = client.post(
            "/auth/token",
            data={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert token_resp.status_code == 200
        token = token_resp.json()["access_token"]

        me_resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200
        assert me_resp.json()["role"] == "admin"
    finally:
        object.__setattr__(api.settings, "jwt_auth_enabled", original)