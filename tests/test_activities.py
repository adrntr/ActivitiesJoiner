from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock, ANY

import pytest
from starlette import status

from models import Location
from schemas.activities import ActivityResponse
from tests.conftest import session, client, user, user_b
import crud.activities as crud_activities



# Get Activity
def test_get_activity_not_found(session, client, user):
    response = client.get("/activities/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_activity_found(session, client, user, activity_without_participants):
    response = client.get(f"/activities/{activity_without_participants.id}")
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


def test_get_activities_not_empty(session, client, user, activity_without_participants):
    response = client.get("/activities", params={"creator_id": activity_without_participants.creator_id,
                                                 "start_after": datetime.now() - timedelta(hours=2)})
    data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert len(data) == 1
    assert isinstance(data, list)
    assert data[0]["description"] == activity_without_participants.description
    assert data[0]["max_participants"] == activity_without_participants.max_participants
    assert not data[0]["participants"]
    assert data[0]["location"]["name"] == activity_without_participants.location.name
    assert datetime.fromisoformat(data[0]["start_datetime"]) == activity_without_participants.start_datetime
    assert datetime.fromisoformat(data[0]["end_datetime"]) == activity_without_participants.end_datetime


# create activity
def build_activity_body(
        description="Activity test",
        max_participants=10,
        location=None,
        start_datetime=None,
        end_datetime=None,
):
    location = location or {"name": "Test Location"}
    start_datetime = start_datetime or datetime.now(timezone.utc).isoformat()
    end_datetime = end_datetime or (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()

    return {
        "description": description,
        "max_participants": max_participants,
        "location": location,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
    }


@patch("routers.activities.get_or_create_location", new_callable=AsyncMock)
def test_create_activity(mock_get_location, session, client, user):
    mock_location = Location(id=99, name="Test Location", latitude=40.7128, longitude=-74.0060)
    mock_get_location.return_value = mock_location

    body = build_activity_body()
    response = client.post("/activities", json=body)

    assert response.status_code == status.HTTP_201_CREATED
    mock_get_location.assert_awaited_once_with("Test Location", ANY)


@pytest.mark.parametrize(
    "description, max_participants, location, expected_status, expected_error",
    [
        ("", 10, {"name": "Test Location"}, status.HTTP_422_UNPROCESSABLE_ENTITY, "description"),
        ("Activity test", 0, {"name": "Test Location"}, status.HTTP_422_UNPROCESSABLE_ENTITY, "max_participants"),
        ("Activity test", 10, "Test Location", status.HTTP_422_UNPROCESSABLE_ENTITY, "location"),
    ],
)
def test_create_activity_invalid_inputs(session, client, user, description, max_participants, location, expected_status,
                                        expected_error):
    body = build_activity_body(description=description, max_participants=max_participants, location=location)
    response = client.post("/activities", json=body)
    assert response.status_code == expected_status
    if expected_error:
        assert expected_error.lower() in response.text.lower()


@patch("services.locations.get_latitude_longitude", new_callable=AsyncMock)
def test_create_activity_location_not_found(mock_get_latitude_longitude, session, client, user):
    mock_get_latitude_longitude.return_value = (None, None)

    body = build_activity_body()
    response = client.post("/activities", json=body)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "location not found" in data["error"].lower()


@pytest.mark.parametrize(
    "start_dt, end_dt",
    [
        (datetime.now(timezone(timedelta(hours=-5), 'EST')), datetime.now(timezone.utc) + timedelta(hours=2)),
        (datetime.now(timezone.utc), datetime.now(timezone(timedelta(hours=5), 'EST')) + timedelta(hours=2)),
    ],
)
def test_create_activity_incorrect_datetime_zones(session, client, user, start_dt, end_dt):
    body = build_activity_body(
        start_datetime=start_dt.isoformat(),
        end_datetime=end_dt.isoformat(),
    )
    response = client.post("/activities", json=body)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "datetime must be in utc" in response.text.lower()


# Update Activity
def test_update_activity_not_found(session, client, user):
    response = client.put(f"/activities/999", json={})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_activity_not_owner(session, client, user, activity_without_participants):
    response = client.put(f"/activities/{activity_without_participants.id}", json={})
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_activity_max_participants_error(session, client, user, activity_with_participants):
    activity_with_participants.creator_id = user.id
    activity_with_participants = crud_activities.create(session, activity_with_participants)
    response = client.put(f"/activities/{activity_with_participants.id}", json={"max_participants": 1})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "you cannot remove more people than there are" in response.text.lower()


def test_update_activity_low_end_time(session, client, user, activity_with_participants):
    activity_with_participants.creator_id = user.id
    activity_with_participants = crud_activities.create(session, activity_with_participants)
    response = client.put(f"/activities/{activity_with_participants.id}",
                          json={"end_datetime": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "start datetime must be before end datetime" in response.text.lower()


@patch("services.locations.get_latitude_longitude", new_callable=AsyncMock)
def test_update_activity_ok(mock_get_latitude_longitude, session, client, user, activity_with_participants):
    activity_with_participants.creator_id = user.id
    activity_with_participants = crud_activities.create(session, activity_with_participants)
    mock_get_latitude_longitude.return_value = (13.123, 13.123)
    start_datetime = datetime.now(timezone.utc) - timedelta(hours=2)
    end_datetime = datetime.now(timezone.utc) + timedelta(hours=2)
    response = client.put(f"/activities/{activity_with_participants.id}",
                          json={
                              "location": {"name": "New Location"},
                              "start_datetime": start_datetime.isoformat(),
                              "end_datetime": end_datetime.isoformat(),
                              "description": "New Description",
                              "max_participants": 3,
                          })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["location"]["name"] == "New Location"
    assert data["description"] == "New Description"
    assert data["max_participants"] == 3
    assert data["start_datetime"] == start_datetime.isoformat()
    assert data["end_datetime"] == end_datetime.isoformat()


# Join Activity

def test_join_activity_not_found(session, client, user):
    response = client.post("/activities/999/participants")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_join_activity_full(session, client, user, activity_with_participants):
    # Make the activity to be full
    activity_with_participants.creator_id = user.id
    activity_with_participants = crud_activities.create(session, activity_with_participants)
    response = client.put(f"/activities/{activity_with_participants.id}",
                          json={"max_participants": len(activity_with_participants.participants)})
    assert response.status_code == status.HTTP_200_OK
    # Try to join
    response = client.post(f"/activities/{activity_with_participants.id}/participants")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "no free places" in response.text.lower()

def test_join_activity_already_joined(session, client, user, activity_with_participants):
    response = client.post(f"/activities/{activity_with_participants.id}/participants")
    assert response.status_code == status.HTTP_201_CREATED
    response = client.post(f"/activities/{activity_with_participants.id}/participants")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already participated" in response.text.lower()

def test_join_activity_ok(session, client, user, activity_with_participants):
    response = client.post(f"/activities/{activity_with_participants.id}/participants")
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert {"id": user.id, "username": user.username} in data["participants"]


# Leave Activity

def test_leave_activity_not_found(session, client, user, activity_with_participants):
    response = client.delete("/activities/999/participants/1")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "activity" in response.text.lower()

def test_leave_activity_user_not_found(session, client, user, activity_with_participants):
    response = client.delete(f"/activities/{activity_with_participants.id}/participants/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "user does not exist" in response.text.lower()

def test_leave_activity_not_participant(session, client, user, activity_with_participants):
    response = client.delete(f"/activities/{activity_with_participants.id}/participants/{user.id}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "user does not participate" in response.text.lower()

def test_leave_activity_not_owner(session, client, user_b, activity_with_participants):
    participant = activity_with_participants.participants[0]
    response = client.delete(f"/activities/{activity_with_participants.id}/participants/{participant.id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not allowed" in response.text.lower()

def test_leave_activity_ok_participant(session, client, user, activity_with_participants):
    response = client.post(f"/activities/{activity_with_participants.id}/participants")
    assert response.status_code == status.HTTP_201_CREATED
    response = client.delete(f"/activities/{activity_with_participants.id}/participants/{user.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    for participant in data["participants"]:
        assert participant["id"] != user.id

def test_leave_activity_ok_owner(session, client, user, activity_with_participants):
    activity_with_participants.creator_id = user.id
    activity_with_participants = crud_activities.create(session, activity_with_participants)
    participant_to_delete = activity_with_participants.participants[0]
    response = client.delete(f"/activities/{activity_with_participants.id}/participants/{participant_to_delete.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    for participant in data["participants"]:
        assert participant["id"] != participant_to_delete.id











