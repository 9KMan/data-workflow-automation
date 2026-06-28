"""Pytest configuration and fixtures."""
import os
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Set SQLite file-based URL BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from app.database import Base, get_db
from app.config import Settings
from app.main import app


@pytest.fixture
def test_settings():
    return Settings(
        DATABASE_URL="sqlite:///./test.db",
        API_KEY="test-api-key",
    )


@pytest.fixture
def test_engine():
    """SQLite engine with check_same_thread disabled for test client."""
    engine = create_engine(
        "sqlite:///./test.db",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    # Allow writing from any thread
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db(test_engine):
    """SQLite database for testing."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_client(test_db):
    """FastAPI TestClient with overridden DB dependency."""
    def _override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    from fastapi.testclient import TestClient
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()