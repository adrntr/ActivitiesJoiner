import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from starlette.testclient import TestClient

from core.config import settings
from database import Base
from main import app
from routers.deps import get_db
from models import User
from services.auth import bcrypt_context, get_current_user


@pytest.fixture(scope="session", autouse=True)
def verify_test_env():
    assert settings.ENVIRONMENT == "testing", "Tests must be run with ENVIRONMENT=testing"


@pytest.fixture(scope="session")
def engine():
    return create_engine(settings.database_url)


@pytest.fixture(scope="session", autouse=True)
def prepare_database(engine):
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(bind=connection)
    session = TestingSessionLocal()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(session: Session):
    def get_db_override():
        return session

    app.dependency_overrides[get_db] = get_db_override
    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()

@pytest.fixture
def user(session: Session):
    def get_current_user_override():
        return {"username": "waltest", "user_id": user.id}
    user = User(username="waltest", hashed_password=bcrypt_context.hash("fakepassword"))
    session.add(user)
    session.commit()
    session.refresh(user)
    app.dependency_overrides[get_current_user] = get_current_user_override
    yield user
    app.dependency_overrides.clear()
