import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app, create_app
from app.repositories.sqlite_incidents import SQLiteIncidentRepository
from app.security import create_session

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/v1/auth/login",
            json={"username": "official@roadsense.local", "password": "RoadSense-Demo-2026!"},
        )
        assert response.status_code == 200
        yield test_client


def test_health_endpoint() -> None:
    with TestClient(app) as test_client:
        response = test_client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_incident_list_returns_demo_records(client: TestClient) -> None:
    response = client.get("/api/v1/incidents")

    assert response.status_code == 200
    incidents = response.json()
    assert len(incidents) == 12
    assert all(incident["is_demo"] for incident in incidents)


def test_camera_endpoint_reports_unconfigured_adapter(client: TestClient) -> None:
    response = client.get("/api/v1/incidents/RW-2026-00412/camera-check")

    assert response.status_code == 200
    assert response.json()["status"] == "not_configured"
    assert "No camera feed was queried" in response.json()["detail"]


def test_estimate_endpoint_returns_range_and_assumptions(client: TestClient) -> None:
    response = client.post(
        "/api/v1/incidents/estimate",
        json={"area_m2": 1.8, "depth_cm": 9.4, "road_class": "arterial"},
    )

    assert response.status_code == 200
    estimate = response.json()
    assert estimate["low_inr"] < estimate["midpoint_inr"] < estimate["high_inr"]
    assert estimate["is_demo"]
    assert any("approved municipal rate card" in item for item in estimate["assumptions"])


def test_android_form_locations_are_saved_and_grouped(tmp_path) -> None:
    database_path = tmp_path / "android.sqlite3"
    test_app = create_app(database_path)
    with TestClient(test_app) as test_client:
        test_client.post(
            "/api/v1/auth/login",
            json={"username": "official@roadsense.local", "password": "RoadSense-Demo-2026!"},
        )
        initial_location_count = len(test_client.get("/pothole_locations.json").json())
        first = test_client.post(
            "/pothole_locations",
            data={
                "pothole_location[latitude]": "13.0001",
                "pothole_location[longitude]": "77.0001",
            },
        )
        second = test_client.post(
            "/pothole_locations",
            data={
                "pothole_location[latitude]": "13.00012",
                "pothole_location[longitude]": "77.00012",
            },
        )

        assert first.status_code == second.status_code == 201
        assert first.json() == "Location recorded"
        locations = test_client.get("/pothole_locations.json").json()
        assert len(locations) == initial_location_count + 2
        assert {"latitude", "longitude", "date_time"} <= locations[0].keys()

        incidents = test_client.get("/api/v1/incidents").json()
        uploaded = [incident for incident in incidents if not incident["is_demo"]]
        assert len(uploaded) == 1
        assert uploaded[0]["report_count"] == 2

    reopened_repository = test_app.state.incident_repository.__class__(database_path)
    assert reopened_repository.get_incident(uploaded[0]["id"]).report_count == 2


def test_location_event_id_prevents_duplicate_observation(tmp_path) -> None:
    test_app = create_app(tmp_path / "idempotency.sqlite3")
    payload = {
        "latitude": 13.2,
        "longitude": 77.2,
        "source_event_id": "phone-42-frame-8",
    }
    with TestClient(test_app) as test_client:
        test_client.post(
            "/api/v1/auth/login",
            json={"username": "official@roadsense.local", "password": "RoadSense-Demo-2026!"},
        )
        first = test_client.post("/pothole_locations", json=payload)
        retry = test_client.post("/pothole_locations", json=payload)

        assert first.status_code == retry.status_code == 201
        incidents = test_client.get("/api/v1/incidents").json()
        uploaded = [incident for incident in incidents if not incident["is_demo"]]
        assert len(uploaded) == 1
        assert uploaded[0]["report_count"] == 1


def test_official_login_protects_and_releases_dashboard_routes() -> None:
    with TestClient(app) as anonymous_client:
        denied = anonymous_client.get("/api/v1/incidents")
        assert denied.status_code == 401

        rejected_login = anonymous_client.post(
            "/api/v1/auth/login",
            json={"username": "official@roadsense.local", "password": "wrong-password"},
        )
        assert rejected_login.status_code == 401

        successful_login = anonymous_client.post(
            "/api/v1/auth/login",
            json={"username": "official@roadsense.local", "password": "RoadSense-Demo-2026!"},
        )
        assert successful_login.status_code == 200
        assert successful_login.json()["role"] == "official"
        assert anonymous_client.get("/api/v1/auth/me").status_code == 200
        assert anonymous_client.get("/api/v1/incidents").status_code == 200

        assert anonymous_client.post("/api/v1/auth/logout").status_code == 204
        assert anonymous_client.get("/api/v1/incidents").status_code == 401


def test_geographic_seed_migration_is_idempotent(tmp_path) -> None:
    repository = SQLiteIncidentRepository(tmp_path / "seed.sqlite3")
    repository.initialize()
    first_run = repository.list_incidents()
    repository.initialize()
    second_run = repository.list_incidents()

    assert len(first_run) == len(second_run) == 12
    assert {"Bengaluru", "Coimbatore"} <= {
        "Coimbatore" if "Coimbatore" in incident.road_name else "Bengaluru"
        for incident in first_run
        if "Bengaluru" in incident.road_name or "Coimbatore" in incident.road_name
    }


def test_production_rejects_example_session_secret(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SESSION_SECRET", "replace-with-a-long-random-local-secret")

    with pytest.raises(HTTPException, match="strong production session secret"):
        create_session("official@example.gov")
