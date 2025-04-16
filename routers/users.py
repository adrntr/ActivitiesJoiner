from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from database import get_session
from services.auth import get_current_user
import crud.users as crud_users
router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get("/{user_id}", status_code=status.HTTP_200_OK)
async def read_user(user_id, db: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    # TODO: Define who is allowed to see other users
    return crud_users.get_by_id(db, user_id)

