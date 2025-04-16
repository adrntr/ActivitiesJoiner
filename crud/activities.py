from sqlalchemy.orm import Session

from models import Activity, User


def get_all(session):
    return session.query(Activity).all()

def get_by_id(session, activity_id):
    return session.query(Activity).filter_by(id=activity_id).first()

def create(session: Session, activity: Activity):
    session.add(activity)
    session.commit()
    session.refresh(activity)
    return activity

def add_participant(session: Session, activity: Activity, user: User):
    activity.participants.append(user)
    session.commit()
    session.refresh(activity)
    return activity

def delete_participant(session: Session, activity: Activity, user: User):
    activity.participants.remove(user)
    session.commit()
    session.refresh(activity)
    return activity

