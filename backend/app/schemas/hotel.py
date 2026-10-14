import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class SearchCenter(BaseModel):
    latitude: float
    longitude: float
    city: Optional[str] = None
    state: Optional[str] = None
    postcode: str
    country: str = "United States"
    formatted: Optional[str] = None

class HotelPlace(BaseModel):
    place_id: str
    name: str = Field(default="Name not provided")
    formatted_address: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postcode: Optional[str] = None
    latitude: float
    longitude: float
    distance_meters: Optional[float] = None
    distance_km: Optional[float] = None
    category: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    is_shortlisted: bool = False

    @field_validator("name", mode="before")
    @classmethod
    def ensure_honest_name(cls, v):
        if not v or not str(v).strip():
            return "Name not provided"
        return str(v).strip()

class HotelSearchResponse(BaseModel):
    zip_code: str
    search_center: SearchCenter
    radius_km: float = 5.0
    total: int
    results: list[HotelPlace]

class ShortlistCreateRequest(BaseModel):
    place_id: str
    name: str
    formatted_address: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postcode: Optional[str] = None
    latitude: float
    longitude: float
    distance_meters: Optional[float] = None
    category: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    search_zip: Optional[str] = None

class ShortlistResponse(BaseModel):
    shortlist: list[HotelPlace]
    total: int

class GenericMessageResponse(BaseModel):
    message: str
    status: str = "ok"
