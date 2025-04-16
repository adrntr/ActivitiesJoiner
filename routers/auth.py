from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session
from starlette import status
from typing_extensions import Annotated

from database import get_session
from models import User
from schemas.auth import RegisterRequest
import crud.users as crud_users
from schemas.users import UserOut
from services.auth import bcrypt_context, authenticate_user, create_token

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserOut)
async def register(register_request: RegisterRequest, session: Session = Depends(get_session)):
    create_user_dict = register_request.model_dump()
    existing_user = crud_users.get_by_username(session, create_user_dict['username'])
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail='username already registered')
    create_user_dict["hashed_password"] = bcrypt_context.hash(register_request.password)
    create_user_dict.pop('password')
    new_user = User(**create_user_dict)
    return crud_users.create_user(session, new_user)

@router.post("/token")
async def create_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                              session: Session = Depends(get_session)):
    user = authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password")
    token = create_token(user.username, user.id)
    return {"access_token": token, "token_type": "bearer"}