from fastapi import Depends
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
import crud.users as crud_users
from database import get_session

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
# oauth2_bearer gets the token from auth/token enpoint
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')
SECRET_KEY = '0a5fe037e6efb46e6bb54f6a66b2c5b239a82a7dcca78368bfc46141cbaff23f'
ALGORITHM = 'HS256'

def authenticate_user(username: str, password: str, session: Session = Depends(get_session())):
    """
    Return the user from the database if it exist and the password is correct.
    """
    user = crud_users.get_by_username(session, username)
    if not user:
        return None
    if not bcrypt_context.verify(password, user.hashed_password):
        return None
    return user

def create_token(username: str, user_id: str):
    """
    Creates a JWT token to authenticate a user.
    sub: subject
    """
    encode = {'sub': username, "id": user_id}
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_bearer)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Incorrect username or password')
        return {'username': username, 'user_id': user_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate credentials')
