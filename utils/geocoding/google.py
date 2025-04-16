import httpx
import os
from .base import Geocoder

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class GoogleGeocoder(Geocoder):
    async def geocode(self, name: str):
        if not GOOGLE_API_KEY:
            raise ValueError("Missing GOOGLE_API_KEY in environment")

        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": name, "key": GOOGLE_API_KEY}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            if data["status"] == "OK":
                loc = data["results"][0]["geometry"]["location"]
                return loc["lat"], loc["lng"]
            return None, None

# TODO: not tested