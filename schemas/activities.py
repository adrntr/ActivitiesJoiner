from datetime import datetime
from pydantic import BaseModel, model_validator, field_validator
from typing import List, Optional
from schemas.users import UserOut


class LocationRequest(BaseModel):
    name: str


class LocationResponse(BaseModel):
    name: str
    latitude: float
    longitude: float

    class Config:
        from_attributes = True


class ActivityCreationRequest(BaseModel):
    description: str
    max_participants: int
    location: LocationRequest
    start_datetime: datetime
    end_datetime: datetime

    @field_validator("start_datetime", "end_datetime")
    @classmethod
    def ensure_timezone_aware(cls, value: datetime, info):
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError(f"{info.field_name} must include a timezone (e.g., use 'Z' or '+00:00')")
        return value

    @model_validator(mode='after')
    def validate_dates(self):
        if self.start_datetime > self.end_datetime:
            raise ValueError('start_date must be before end_date')
        return self


class ActivityResponse(BaseModel):
    id: int
    description: str
    max_participants: int
    creator: UserOut
    participants: List[UserOut]
    location: Optional[LocationResponse]
    start_datetime: datetime
    end_datetime: datetime

    class Config:
        from_attributes = True
