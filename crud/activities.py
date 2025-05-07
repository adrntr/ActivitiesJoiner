from sqlalchemy.orm import Session

from models import Activity, User
from schemas.activities import ActivityFilter


def get_all(session):
    return session.query(Activity).all()


def get_by_id(session, activity_id):
    return session.query(Activity).filter_by(id=activity_id).first()


def create(session: Session, activity: Activity):
    session.add(activity)
    session.commit()
    session.refresh(activity)
    return activity


def search(session: Session, filters: ActivityFilter):
    query = session.query(Activity)
    if filters.creator_id:
        query = query.filter(Activity.creator_id == filters.creator_id)
    if filters.description:
        query = query.filter(Activity.description.like(f'%{filters.description}%'))
    if filters.start_after:
        query = query.filter(Activity.start_datetime >= filters.start_after)
    if filters.end_before:
        query = query.filter(Activity.end_datetime <= filters.end_before)
    if filters.min_free_places:
        query = query.filter(Activity.free_places >= filters.min_free_places)
    column_order_by = getattr(Activity, filters.order_by)
    query = query.order_by(column_order_by.desc())
    return query.offset(filters.offset).limit(filters.limit).all()


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
