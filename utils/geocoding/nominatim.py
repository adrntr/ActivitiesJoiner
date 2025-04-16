import httpx
from .base import Geocoder

class NominatimGeocoder(Geocoder):
    async def geocode(self, name: str):
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": name, "format": "json", "limit": 5}
        headers = {"User-Agent": "YourAppName/1.0"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            data = response.json()
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
            return None, None