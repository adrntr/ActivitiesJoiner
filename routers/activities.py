from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session
from starlette import status

from routers.deps import get_db
from models import Activity
from schemas.activities import ActivityCreationRequest, ActivityResponse, ActivityUpdateRequest, ActivityFilter
import crud.activities as crud_activities
import crud.users as crud_users
from services.auth import get_current_user
from services.locations import get_or_create_location

router = APIRouter(
    prefix="/activities",
    tags=["activities"],
)


@router.get("/{activity_id}", status_code=status.HTTP_200_OK, response_model=ActivityResponse)
async def get_activity(activity_id: int, session: Session = Depends(get_db),
                       user: dict = Depends(get_current_user)):
    activity = crud_activities.get_by_id(session, activity_id)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    return activity


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[ActivityResponse])
async def get_activities(filters: ActivityFilter = Depends(), session: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return crud_activities.search(session, filters)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ActivityResponse)
async def create_activity(activity_creation_request: ActivityCreationRequest, session: Session = Depends(get_db),
                          user: dict = Depends(get_current_user)):
    location_model = await get_or_create_location(activity_creation_request.location.name, session)
    activity_model = Activity(creator_id=user["user_id"],
                              description=activity_creation_request.description,
                              max_participants=activity_creation_request.max_participants,
                              location=location_model,
                              start_datetime=activity_creation_request.start_datetime,
                              end_datetime=activity_creation_request.end_datetime)
    return crud_activities.create(session, activity_model)

@router.put("/{activity_id}", status_code=status.HTTP_200_OK, response_model=ActivityResponse)
async def update_activity(activity_id: int, activity_update_request: ActivityUpdateRequest, session: Session = Depends(get_db),
                          user: dict = Depends(get_current_user)):
    activity_model = crud_activities.get_by_id(session, activity_id)
    if not activity_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    if activity_model.creator_id != user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to edit this activity")
    if activity_update_request.max_participants and activity_update_request.max_participants < len(activity_model.participants):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot remove more people than there are")
    if activity_update_request.location:
        location_model = await get_or_create_location(activity_update_request.location.name, session)
        activity_model.location = location_model

    start = activity_update_request.start_datetime or activity_model.start_datetime
    end = activity_update_request.end_datetime or activity_model.end_datetime

    if start >= end:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Start datetime must be before end datetime")

    activity_model.start_datetime = start
    activity_model.end_datetime = end

    activity_model.description = activity_update_request.description if activity_update_request.description else activity_model.description
    activity_model.max_participants = activity_update_request.max_participants if activity_update_request.max_participants else activity_model.max_participants

    return crud_activities.create(session, activity_model)


@router.post("/{activity_id}/participants", status_code=status.HTTP_201_CREATED, response_model=ActivityResponse)
async def join_activity(activity_id: int, session: Session = Depends(get_db),
                        user: dict = Depends(get_current_user)):
    # TODO: Other users can add other people
    activity_model = crud_activities.get_by_id(session, activity_id)
    if not activity_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    if not activity_model.free_places:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No free places available")
    user_model = crud_users.get_by_id(session, user["user_id"])
    if user_model in activity_model.participants:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already participated")
    return crud_activities.add_participant(session, activity_model, user_model)


@router.delete("/{activity_id}/participants/{user_id}", status_code=status.HTTP_200_OK, response_model=ActivityResponse)
async def leave_activity(activity_id: int, user_id: int, session: Session = Depends(get_db),
                         user: dict = Depends(get_current_user)):
    current_user =  crud_users.get_by_id(session, user.get("user_id"))
    activity_model = crud_activities.get_by_id(session, activity_id)
    if not activity_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    user_to_remove = crud_users.get_by_id(session, user_id)
    if not user_to_remove:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")
    if not user_to_remove in activity_model.participants:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User does not participate")
    if user_to_remove.id != current_user.id and current_user != activity_model.creator:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to remove the user")
    return crud_activities.delete_participant(session, activity_model, user_to_remove)
