from sqlalchemy import Column, String, Integer, ForeignKey, Table, select, func, Float
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from database import Base

activity_participants = Table(
    "activity_participants", Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("activity_id", Integer, ForeignKey("activities.id"))
)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    activities_joined = relationship("Activity", secondary="activity_participants", back_populates="participants")
    activities_created = relationship("Activity", back_populates="creator")


class Activity(Base):
    __tablename__ = 'activities'
    id = Column(Integer, primary_key=True)
    description = Column(String(255), nullable=False)
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    max_participants = Column(Integer, nullable=False, default=1000)
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=True)

    creator = relationship("User", back_populates="activities_created")
    participants = relationship("User", secondary="activity_participants", back_populates="activities_joined")
    location = relationship("Location", back_populates="activities")

    @hybrid_property
    def free_places(self):
        return self.max_participants - len(self.participants)

    @free_places.expression
    def free_places(cls):
        return (
            cls.max_participants -
            select(func.count(activity_participants.c.user_id)).where(activity_participants.c.activiy_id == cls.id).correlate(cls).scalar_subquery()
        )

class Location(Base):
    __tablename__ = 'locations'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)  # e.g., "Central Park"
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    activities = relationship("Activity", back_populates="location")



