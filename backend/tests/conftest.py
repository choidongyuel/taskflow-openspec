import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture()
def db_session():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    # Intentionally not using `with TestClient(app) as test_client` here:
    # entering the context triggers the app's startup event, which calls
    # Base.metadata.create_all() against the real production engine
    # (app.database.engine), touching the dev taskflow.db file. The test
    # DB schema is already created explicitly in db_session above.
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def signup_and_login(client: TestClient, email: str = "user@example.com", password: str = "password123") -> dict:
    resp = client.post("/auth/signup", json={"email": email, "password": password})
    assert resp.status_code == 201, resp.text
    return resp.json()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def signed_up_user(client):
    return signup_and_login(client)


@pytest.fixture()
def team_owner_with_team(client):
    user = signup_and_login(client, email="owner@example.com")
    headers = auth_headers(user["token"])
    resp = client.post("/teams", json={"name": "Frontiers"}, headers=headers)
    assert resp.status_code == 201, resp.text
    team = resp.json()
    return {"user": user, "headers": headers, "team": team}
