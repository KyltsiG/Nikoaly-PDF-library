"""
Phase 1 Tests — PDF ingestion and metadata storage.
Run with: pytest tests/
"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.pool import StaticPool

from backend.main import app
from backend.db.database import get_session


# --- Test DB setup (in-memory SQLite) ---

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# --- Tests ---

def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_non_pdf_rejected(client: TestClient):
    response = client.post(
        "/api/pdfs/upload",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 400


def test_list_pdfs_empty(client: TestClient):
    response = client.get("/api/pdfs/")
    assert response.status_code == 200
    assert response.json() == []


def test_get_nonexistent_pdf(client: TestClient):
    response = client.get("/api/pdfs/999")
    assert response.status_code == 404
