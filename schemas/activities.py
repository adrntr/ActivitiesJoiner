from pydantic import BaseModel
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




class ActivityResponse(BaseModel):
    id: int
    description: str
    max_participants: int
    creator: UserOut
    participants: List[UserOut]
    location: Optional[LocationResponse]

    class Config:
        from_attributes = True




