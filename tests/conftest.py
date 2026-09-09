import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test_secret_for_unit_tests_12345"

from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.auth.security import get_password_hash, create_access_token

# In-memory SQLite engine for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Creates a fresh database schema for every test function."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def admin_user(db_session) -> User:
    user = User(
        username="admin_test",
        email="admin@ofi.com",
        full_name="Admin Test",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def supervisor_user(db_session) -> User:
    user = User(
        username="supervisor_test",
        email="supervisor@ofi.com",
        full_name="Supervisor Test",
        hashed_password=get_password_hash("password123"),
        role=UserRole.SUPERVISOR,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def officer_user(db_session) -> User:
    user = User(
        username="officer_test",
        email="officer@ofi.com",
        full_name="Officer Test",
        hashed_password=get_password_hash("password123"),
        role=UserRole.WAREHOUSE_OFFICER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def viewer_user(db_session) -> User:
    user = User(
        username="viewer_test",
        email="viewer@ofi.com",
        full_name="Viewer Test",
        hashed_password=get_password_hash("password123"),
        role=UserRole.VIEWER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_headers(admin_user) -> dict:
    token = create_access_token(subject=admin_user.id, role=admin_user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def supervisor_headers(supervisor_user) -> dict:
    token = create_access_token(subject=supervisor_user.id, role=supervisor_user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def officer_headers(officer_user) -> dict:
    token = create_access_token(subject=officer_user.id, role=officer_user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def viewer_headers(viewer_user) -> dict:
    token = create_access_token(subject=viewer_user.id, role=viewer_user.role.value)
    return {"Authorization": f"Bearer {token}"}
