from typing import Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

import crud.locations as crud_locations
from models import Location
from utils.geocoding.service import get_geocoder

GEOCODER = "nominatim"


async def get_latitude_longitude(name) -> Tuple[float, float]:
    return await get_geocoder(GEOCODER).geocode(name)


async def get_or_create_location(name: str, session: Session) -> Location:
    latitude, longitude = await get_latitude_longitude(name)
    # If this function is not used by a router this should be refactored.
    if not latitude or not longitude:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Location not found"
        )
    if existing_location := crud_locations.get_location(session, latitude, longitude):
        return existing_location

    return crud_locations.create_location(session, name, latitude, longitude)
