from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock, ANY

import pytest
from starlette import status

from models import Location
from schemas.activities import ActivityResponse
from tests.conftest import session, client, user


# Get Activity
def test_get_activity_not_found(session, client, user):
    response = client.get("/activities/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_activity_found(session, client, user, activity):
    response = client.get(f"/activities/{activity.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    activity_response = ActivityResponse(**data)  # pydantic validation


def test_get_activity_incorrect_user(session, client, incorrect_user):
    response = client.get(f"/activities/999")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# get_activities

@pytest.mark.parametrize(
    "query_params, expected_status",
    [
        ({"limit": 10}, 200),
        ({"limit": 101}, 422),  # Over max limit
        ({"offset": -1}, 422),  # Invalid offset
        ({"order_by": "end_datetime"}, 200),
        ({"order_by": "invalid_field"}, 422),  # Invalid order_by
        ({"creator_id": 1, "min_free_places": 5}, 200),
        ({"creator_id": "abc"}, 422),  # Invalid creator_id (not int)
        ({"description": "Yoga"}, 200),
        ({"start_after": "2025-01-01T00:00:00"}, 200),
        ({"start_after": "invalid-date"}, 422),  # Invalid datetime
        ({"end_before": "2025-12-31T23:59:59"}, 200),
        ({"end_before": "not-a-date"}, 422),  # Invalid end_before
    ]
)
def test_get_activities(session, client, user, query_params, expected_status):
    response = client.get("/activities/", params=query_params)
    assert response.status_code == expected_status


def test_get_activities_empty(session, client, user):
    response = client.get("/activities", params={"creator_id": 999})
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_get_activities_not_empty(session, client, user, activity):
    response = client.get("/activities", params={"creator_id": activity.creator_id,
                                                 "start_after": datetime.now() - timedelta(hours=2)})
    data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert len(data) == 1
    assert isinstance(data, list)
    assert data[0]["description"] == activity.description
    assert data[0]["max_participants"] == activity.max_participants
    assert not data[0]["participants"]
    assert data[0]["location"]["name"] == activity.location.name
    assert datetime.fromisoformat(data[0]["start_datetime"]) == activity.start_datetime
    assert datetime.fromisoformat(data[0]["end_datetime"]) == activity.end_datetime


# create activity
@patch("routers.activities.get_or_create_location", new_callable=AsyncMock)
def test_create_activity(mock_get_location, session, client, user):
    mock_location = Location(id=99, name="Test Location", latitude=40.7128, longitude=-74.0060)
    mock_get_location.return_value = mock_location
    body = {"description": "activity test",
            "max_participants": 10,
            "location": {"name": "Test Location"},
            "start_datetime": datetime.now(timezone.utc).isoformat(),
            "end_datetime": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()}
    response = client.post("/activities", json=body)
    assert response.status_code == status.HTTP_201_CREATED
    mock_get_location.assert_awaited_once_with("Test Location", ANY)
