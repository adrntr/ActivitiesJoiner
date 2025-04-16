from typing import Optional

from sqlalchemy.orm import Session

from models import User


def get_by_id(session: Session, user_id: int) -> Optional[User]:
    return session.query(User).filter(user_id == User.id).first()

def get_by_username(session: Session, username: str) -> Optional[User]:
    return session.query(User).filter(username == User.username).first()

def create_user(session: Session, user: User) -> User:
    session.add(user)
    session.commit()
    session.refresh(user)
    return user