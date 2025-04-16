from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from models import Location
from .google import GoogleGeocoder
from .nominatim import NominatimGeocoder
from .base import Geocoder

def get_geocoder(provider: str = "nominatim") -> Geocoder:
    if provider == "google":
        return GoogleGeocoder()
    if provider == "nominatim":
        return NominatimGeocoder()
    return NominatimGeocoder()

