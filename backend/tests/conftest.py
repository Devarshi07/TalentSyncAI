"""
Shared test fixtures for API integration tests.
Uses an in-memory SQLite database for isolation.
"""
import os

# MUST set env vars BEFORE any app imports
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["GEMINI_API_KEY"] = ""
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["RATE_LIMIT_PER_MINUTE"] = "10000"
os.environ["JWT_SECRET"] = "test-secret-key"
os.environ["DEBUG"] = "true"
os.environ["GOOGLE_CLIENT_ID"] = ""
os.environ["GOOGLE_CLIENT_SECRET"] = ""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db.database import Base, get_db
from app import app
from core.limiter import limiter

# Disable rate limiting for tests
limiter.enabled = False

# In-memory SQLite for tests
engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Create a user and return auth headers."""
    resp = client.post("/api/auth/signup", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123",
    })
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_user_headers(client):
    """Create a second user for isolation tests."""
    resp = client.post("/api/auth/signup", json={
        "username": "otheruser",
        "email": "other@example.com",
        "password": "OtherPass123",
    })
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
