from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

class PlaceExtract(BaseModel):
    """Modelo de dominio para los datos extraídos."""
    place_id: str
    name: str
    place_type: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    price_range: Optional[str] = None
    review_count: Optional[int] = 0
    rating: Optional[float] = None
    hours_json: Optional[dict] = None
