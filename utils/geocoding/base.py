from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple


class Geocoder(ABC):
    @abstractmethod
    async def geocode(self, name: str) -> Tuple[float | None, float | None]:
        pass