import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from starlette.testclient import TestClient
from testcontainers.postgres import PostgresContainer

from database import Base
from main import app
from routers.deps import get_db
from models import User
from services.auth import bcrypt_context, get_current_user


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:15") as container:
        yield container


@pytest.fixture(scope="session")
def engine(postgres_container: PostgresContainer):
    engine = create_engine(postgres_container.get_connection_url())
    return engine


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
