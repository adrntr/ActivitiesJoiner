from starlette import status

import crud.activities as crud_activities
from models import Activity
from tests.conftest import session, client, user


def test_get_activity_not_found(session, client, user):
    response = client.get("/activities/1")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_activity_found(session, client, user):
    activity = Activity(creator_id=user.id, description="test", max_participants=10)
    crud_activities.create(session, activity)
    response = client.get("/activities/1")
    assert response.status_code == status.HTTP_200_OK


def test_get_activities_empty(session, client, user):
    response = client.get("/activities")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_get_activities_not_empty(session, client, user):
    activity = Activity(creator_id=user.id, description="test", max_participants=10)
    crud_activities.create(session, activity)
    response = client.get("/activities")
    data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert len(data) == 1
    assert isinstance(data, list)
    assert data[0]["description"] == "test"

def test_create_activity(session, client, user):
    response = client.post("/activities", json={"description": "test", "max_participants": 10, "location": {"name":"Barcelona"}})
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["description"] == "test"
    assert response.json()["max_participants"] == 10
    assert response.json()["location"]["name"] == "Barcelona"
    assert isinstance(response.json()["location"]["latitude"], float)
    assert isinstance(response.json()["location"]["longitude"], float)

