from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session
from starlette import status

from routers.deps import get_session
from models import Activity
from schemas.activities import ActivityCreationRequest, ActivityResponse
import crud.activities as crud_activities
import crud.users as crud_users
from services.auth import get_current_user
from services.locations import get_or_create_location

router = APIRouter(
    prefix="/activities",
    tags=["activities"],
)

@router.get("/{activity_id}", status_code=status.HTTP_200_OK, response_model=ActivityResponse)
async def get_activity(activity_id: int, session: Session = Depends(get_session),
                       user: dict = Depends(get_current_user)):
    return crud_activities.get_by_id(session, activity_id)

@router.get("/", status_code=status.HTTP_200_OK, response_model=List[ActivityResponse])
async def get_activities(session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    return crud_activities.get_all(session)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ActivityResponse)
async def create_activity(activity_creation_request: ActivityCreationRequest, session: Session = Depends(get_session),
                          user: dict = Depends(get_current_user)):

    location_model = await get_or_create_location(activity_creation_request.location.name, session)
    activity_model = Activity(creator_id=user["user_id"], description=activity_creation_request.description, max_participants=activity_creation_request.max_participants, location=location_model)
    return crud_activities.create(session, activity_model)

@router.post("/{activity_id}/participants", status_code=status.HTTP_201_CREATED, response_model=ActivityResponse)
async def join_activity(activity_id: int, session: Session = Depends(get_session),
                        user: dict = Depends(get_current_user)):
    #TODO: Other users can add other people
    activity_model = crud_activities.get_by_id(session, activity_id)
    if not activity_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Activity not found")
    if not activity_model.free_places:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="No free places available")
    user_model = crud_users.get_by_id(session, user["user_id"])
    if user_model in activity_model.participants:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="User already participated")
    return crud_activities.add_participant(session, activity_model, user_model)


@router.delete("/{activity_id}/participants/{user_id}", status_code=status.HTTP_200_OK, response_model=ActivityResponse)
async def leave_activity(activity_id: int, user_id: int, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    activity_model = crud_activities.get_by_id(session, activity_id)
    if not activity_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Activity not found")
    user_model = crud_users.get_by_id(session, user["user_id"])
    if not user_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User does not exist")
    if not user_model in activity_model.participants:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="User does not participate")
    if user_model.id != user.get("user_id") and user_model != activity_model.creator:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="You are not allowed to remove the user")
    return crud_activities.delete_participant(session, activity_model, user_model)


