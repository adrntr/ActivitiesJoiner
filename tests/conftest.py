from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from starlette import status
from starlette.testclient import TestClient
from testcontainers.postgres import PostgresContainer

from database import Base
from main import app
from routers.deps import get_db
from models import User, Location, Activity
from services.auth import bcrypt_context, get_current_user
import crud.locations as crud_locations
import crud.activities as crud_activities
import crud.users as crud_users


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

@pytest.fixture
def incorrect_user(session: Session):
    def get_current_user_override():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate credentials')

    app.dependency_overrides[get_current_user] = get_current_user_override
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def activity_without_participants(session: Session):
    user = User(username="test_user", hashed_password=bcrypt_context.hash("test_password"))
    user_model = crud_users.create(session, user)
    location = Location(name="test location", latitude=37.7749, longitude=-122.4194)
    location_model = crud_locations.create(session, location)
    activity = Activity(description="test activity",
                        max_participants=10,
                        creator_id=user_model.id,
                        location_id=location_model.id,
                        start_datetime=datetime.now(timezone.utc),
                        end_datetime=datetime.now(timezone.utc) + timedelta(hours=2))
    activity_model = crud_activities.create(session, activity)
    return activity_model

@pytest.fixture
def activity_with_participants(session: Session, user: User):
    user_a = User(username="test_user_a", hashed_password=bcrypt_context.hash("test_password"))
    user_model_a = crud_users.create(session, user_a)
    user_b = User(username="test_user_b", hashed_password=bcrypt_context.hash("test_password"))
    user_model_b = crud_users.create(session, user_b)
    location = Location(name="test location", latitude=37.7749, longitude=-122.4194)
    location_model = crud_locations.create(session, location)
    activity = Activity(description="test activity",
                        max_participants=10,
                        creator_id=user.id,
                        location_id=location_model.id,
                        start_datetime=datetime.now(timezone.utc),
                        end_datetime=datetime.now(timezone.utc) + timedelta(hours=2))
    activity_model = crud_activities.create(session, activity)
    crud_activities.add_participant(session, activity, user_model_a)
    crud_activities.add_participant(session, activity, user_model_b)
    return activity_model

