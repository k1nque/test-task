"""Test suite for FastAPI application and utilities."""
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
import sys
import asyncio
import logging

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.core.config import settings  # noqa: E402
from app.core.security import verify_api_key  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.models.models import Activity as ActivityModel  # noqa: E402
from app.models.models import Building as BuildingModel  # noqa: E402
from app.models.models import Organization as OrganizationModel  # noqa: E402
from main import app, _resolve_log_level  # noqa: E402

client = TestClient(app)


class FakeQuery:
    """A lightweight stand-in for SQLAlchemy query objects."""

    def __init__(self, items):
        self._items = list(items)
        self._filtered = list(items)
        self._offset = 0
        self._limit = None

    def count(self):
        return len(self._filtered)

    def filter(self, expression):
        attr = getattr(expression.left, "name", getattr(expression.left, "key", None))
        value = getattr(expression.right, "value", expression.right)
        if isinstance(value, (list, tuple, set)):
            values = set(value)
            self._filtered = [item for item in self._filtered if getattr(item, attr) in values]
        else:
            self._filtered = [item for item in self._filtered if getattr(item, attr) == value]
        return self

    def options(self, *args, **kwargs):
        return self

    def join(self, *args, **kwargs):
        return self

    def distinct(self):
        return self

    def order_by(self, *columns):
        for column in reversed(columns):
            attr = getattr(column, "name", getattr(column, "key", None))
            self._filtered.sort(key=lambda item: getattr(item, attr))
        return self

    def offset(self, value):
        self._offset = value
        return self

    def limit(self, value):
        self._limit = value
        return self

    def all(self):
        items = self._filtered[self._offset:]
        if self._limit is not None:
            items = items[:self._limit]
        return items

    def first(self):
        items = self.all()
        return items[0] if items else None


class FakeExecutionResult:
    """Represents the result of a simplified SQL execution."""

    def __init__(self, payload):
        self._payload = payload

    def first(self):
        return self._payload


class FakeSession:
    """Fake database session that returns deterministic data for tests."""

    def __init__(self, data_map, execute_map=None, start_pk=1):
        self._data_map = data_map
        self._execute_map = execute_map or {}
        self._next_pk = start_pk

    def query(self, model):
        return FakeQuery(self._data_map.get(model, []))

    def execute(self, _statement, params):
        payload = self._execute_map.get(params.get("id"))
        return FakeExecutionResult(payload)

    def close(self):
        pass

    def add(self, obj):
        if getattr(obj, "id", None) is None:
            obj.id = self._next_pk
            self._next_pk += 1

        now = datetime.now(UTC)
        if getattr(obj, "created_at", None) is None:
            obj.created_at = now
        if getattr(obj, "updated_at", None) is None:
            obj.updated_at = now

        model = type(obj)
        self._data_map.setdefault(model, []).append(obj)

        if hasattr(obj, "coordinates"):
            desc = getattr(getattr(obj, "coordinates", None), "desc", None)
            if desc and obj.id not in self._execute_map:
                try:
                    coords = desc.strip().removeprefix("POINT(").removesuffix(")")
                except AttributeError:  # Python <3.9 safeguard
                    coords = desc.strip()[6:-1]
                lon_str, lat_str = coords.split()
                self._execute_map[obj.id] = SimpleNamespace(
                    lat=float(lat_str),
                    lon=float(lon_str),
                )

    def commit(self):
        pass

    def refresh(self, _obj):
        pass


@contextmanager
def override_db(session):
    """Temporarily override the database dependency with a fake session."""

    def _override():
        yield session

    app.dependency_overrides[get_db] = _override
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_root_endpoint_returns_service_metadata():
    """Root endpoint should expose API metadata without auth."""
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "Organizations Directory API"
    assert payload["version"] == settings.VERSION
    assert payload["docs"] == "/docs"
    assert payload["redoc"] == "/redoc"


def test_health_endpoint_reports_status():
    """Health endpoint should return a simple healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_resolve_log_level_with_valid_input():
    """Valid log level names should map to the corresponding logging constants."""
    level, invalid = _resolve_log_level("debug")
    assert level == logging.DEBUG
    assert invalid is False


def test_resolve_log_level_with_invalid_input():
    """Unknown log level names should fall back to INFO and flag the issue."""
    level, invalid = _resolve_log_level("not-a-level")
    assert level == logging.INFO
    assert invalid is True


def test_verify_api_key_accepts_valid_key():
    """Security helper should allow the configured API key."""
    result = asyncio.run(verify_api_key(settings.API_KEY))
    assert result == settings.API_KEY


def test_verify_api_key_rejects_invalid_key():
    """Security helper should reject invalid keys with a 403 error."""
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(verify_api_key("invalid"))
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Invalid API key"


def test_list_organizations_returns_paginated_results():
    """GET /api/v1/organizations should return organizations with metadata."""
    now = datetime.now(UTC)
    building = SimpleNamespace(
        id=1,
        address="Main St 1",
        coordinates="POINT(0 0)",
        created_at=now,
        updated_at=now,
        latitude=55.0,
        longitude=37.0,
    )
    organizations = [
        SimpleNamespace(
            id=1,
            name="Org One",
            building_id=1,
            building=building,
            phone_numbers=[SimpleNamespace(phone_number="123-456")],
            activities=[],
            created_at=now,
            updated_at=now,
        ),
        SimpleNamespace(
            id=2,
            name="Org Two",
            building_id=1,
            building=building,
            phone_numbers=[SimpleNamespace(phone_number="987-654")],
            activities=[],
            created_at=now,
            updated_at=now,
        ),
    ]
    session = FakeSession({OrganizationModel: organizations})

    with override_db(session):
        response = client.get(
            "/api/v1/organizations",
            headers={"X-API-Key": settings.API_KEY},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert len(payload["organizations"]) == 2
    assert payload["organizations"][0]["name"] == "Org One"


def test_get_organization_by_id_returns_single_entry():
    """GET /api/v1/organizations/{id} should return a single organization."""
    now = datetime.now(UTC)
    building = SimpleNamespace(
        id=5,
        address="Elm St 5",
        coordinates="POINT(1 1)",
        created_at=now,
        updated_at=now,
        latitude=50.0,
        longitude=40.0,
    )
    organization = SimpleNamespace(
        id=10,
        name="Solo Org",
        building_id=5,
        building=building,
        phone_numbers=[SimpleNamespace(phone_number="555-0101")],
        activities=[],
        created_at=now,
        updated_at=now,
    )
    session = FakeSession({OrganizationModel: [organization]})

    with override_db(session):
        response = client.get(
            "/api/v1/organizations/10",
            headers={"X-API-Key": settings.API_KEY},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 10
    assert payload["name"] == "Solo Org"
    assert payload["building"]["id"] == 5


def test_list_buildings_returns_coordinates():
    """GET /api/v1/buildings should return resolved coordinates."""
    now = datetime.now(UTC)
    buildings = [
        SimpleNamespace(
            id=1,
            address="Main Campus",
            coordinates="POINT(37.0 55.0)",
            created_at=now,
            updated_at=now,
            latitude=55.0,
            longitude=37.0,
        ),
        SimpleNamespace(
            id=2,
            address="Annex",
            coordinates="POINT(30.0 60.0)",
            created_at=now,
            updated_at=now,
            latitude=60.0,
            longitude=30.0,
        ),
    ]
    execute_map = {
        1: SimpleNamespace(lat=55.0, lon=37.0),
        2: SimpleNamespace(lat=60.0, lon=30.0),
    }
    session = FakeSession({BuildingModel: buildings}, execute_map)

    with override_db(session):
        response = client.get(
            "/api/v1/buildings/",
            headers={"X-API-Key": settings.API_KEY},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert payload["buildings"][0]["latitude"] == 55.0
    assert payload["buildings"][1]["longitude"] == 30.0


def test_get_building_by_id_returns_location():
    """GET /api/v1/buildings/{id} should return a building with coordinates."""
    now = datetime.now(UTC)
    building = SimpleNamespace(
        id=3,
        address="Tower",
        coordinates="POINT(40.0 50.0)",
        created_at=now,
        updated_at=now,
        latitude=50.0,
        longitude=40.0,
    )
    execute_map = {3: SimpleNamespace(lat=50.0, lon=40.0)}
    session = FakeSession({BuildingModel: [building]}, execute_map)

    with override_db(session):
        response = client.get(
            "/api/v1/buildings/3",
            headers={"X-API-Key": settings.API_KEY},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 3
    assert payload["latitude"] == 50.0
    assert payload["longitude"] == 40.0


def test_create_building_persists_coordinates():
    """POST /api/v1/buildings should store coordinates and return the resource."""
    session = FakeSession({BuildingModel: []}, start_pk=10)
    payload = {
        "address": "New Site",
        "latitude": 48.8566,
        "longitude": 2.3522,
    }

    with override_db(session):
        response = client.post(
            "/api/v1/buildings/",
            json=payload,
            headers={"X-API-Key": settings.API_KEY},
        )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 10
    assert body["address"] == payload["address"]
    assert body["latitude"] == pytest.approx(payload["latitude"])
    assert body["longitude"] == pytest.approx(payload["longitude"])

    stored = session._data_map[BuildingModel][0]
    assert stored.address == payload["address"]


def test_list_activities_returns_all_levels():
    """GET /api/v1/activities should return a flat activity list."""
    now = datetime.now(UTC)
    activities = [
        SimpleNamespace(
            id=1,
            name="Root",
            parent_id=None,
            level=1,
            created_at=now,
            updated_at=now,
        ),
        SimpleNamespace(
            id=2,
            name="Child A",
            parent_id=1,
            level=2,
            created_at=now,
            updated_at=now,
        ),
    ]
    session = FakeSession({ActivityModel: activities})

    with override_db(session):
        response = client.get(
            "/api/v1/activities/",
            headers={"X-API-Key": settings.API_KEY},
        )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert {item["id"] for item in payload} == {1, 2}


def test_get_activity_by_id_includes_children():
    """GET /api/v1/activities/{id} should include nested children."""
    now = datetime.now(UTC)
    activities = [
        SimpleNamespace(
            id=1,
            name="Root",
            parent_id=None,
            level=1,
            created_at=now,
            updated_at=now,
        ),
        SimpleNamespace(
            id=2,
            name="Child",
            parent_id=1,
            level=2,
            created_at=now,
            updated_at=now,
        ),
    ]
    session = FakeSession({ActivityModel: activities})

    with override_db(session):
        response = client.get(
            "/api/v1/activities/1",
            headers={"X-API-Key": settings.API_KEY},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 1
    assert payload["children"][0]["id"] == 2
