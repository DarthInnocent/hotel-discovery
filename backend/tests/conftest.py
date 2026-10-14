import pytest
import sqlite3
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

from app.controllers.shortlist_controller import ShortlistController
from app.services.geoapify_service import GeoapifyService
from main import app

@pytest.fixture
def temp_db_path(tmp_path):
    """Provide a temporary database file for test isolation."""
    db_file = tmp_path / "test_shortlist.db"
    return db_file

@pytest.fixture
def test_shortlist_controller(temp_db_path):
    """Provide an initialized ShortlistController pointing to a temporary test DB."""
    controller = ShortlistController(db_path=temp_db_path)
    controller.initialize_database()
    return controller

@pytest.fixture
def test_client(test_shortlist_controller, monkeypatch):
    """Provide a FastAPI TestClient with isolated test database."""
    from app.api import endpoints
    monkeypatch.setattr(endpoints, "get_shortlist_controller", lambda: test_shortlist_controller)
    with TestClient(app) as client:
        yield client
