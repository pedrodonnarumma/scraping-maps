from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

class PlaceExtract(BaseModel):
    """Modelo de dominio para los datos extraídos"""
    place_id: str
    name: str
    type: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    distance_to_target: Optional[float] = None
    phone: Optional[str] = None
    web_page: Optional[str] = None
    social_network: Optional[str] = None
    price_range_min: Optional[float] = None
    price_range_max: Optional[float] = None
    number_reviews: Optional[int] = 0
    avrg_rating: Optional[float] = None
    opening_hours: Optional[dict] = None
