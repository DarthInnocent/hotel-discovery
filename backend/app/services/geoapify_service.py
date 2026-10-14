import math
import re
from typing import Optional
import httpx

from app.core.config import settings
from app.schemas.hotel import SearchCenter, HotelPlace, HotelSearchResponse

class InvalidZipCodeError(Exception):
    """Raised when user enters an invalid 5-digit ZIP code format."""
    pass

class UnresolvedZipCodeError(Exception):
    """Raised when a ZIP code does not resolve to a matching U.S. postcode location."""
    pass

class GeoapifyServiceError(Exception):
    """Raised when the Geoapify API encounters a service failure, network error, or invalid credentials."""
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code

def calculate_haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth in meters."""
    R = 6371000  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 1)

class GeoapifyService:
    """
    Service responsible for interacting with Geoapify Geocoding and Places APIs.
    Preserves strict ZIP matching, honest data representation, and clear error boundaries.
    """

    GEOCODE_URL = "https://api.geoapify.com/v1/geocode/search"
    PLACES_URL = "https://api.geoapify.com/v2/places"

    def __init__(self, api_key: Optional[str] = None, client: Optional[httpx.AsyncClient] = None):
        self.api_key = (api_key if api_key is not None else settings.GEOAPIFY_API_KEY).strip()
        self.client = client

    def validate_zip_code(self, zip_code: str) -> str:
        """
        Validates that the input is a valid 5-digit U.S. ZIP code, preserving leading zeros.
        """
        if not zip_code:
            raise InvalidZipCodeError("Please enter a 5-digit U.S. ZIP code.")
        clean_zip = zip_code.strip()
        if not re.match(r"^\d{5}$", clean_zip):
            raise InvalidZipCodeError(
                f"Invalid ZIP code '{zip_code}'. U.S. ZIP codes must be exactly 5 numeric digits (including leading zeros)."
            )
        return clean_zip

    async def geocode_us_zip(self, zip_code: str) -> SearchCenter:
        """
        Resolves a 5-digit U.S. ZIP code to a U.S. postcode location.
        Ensures the lookup strictly establishes the requested U.S. ZIP code.
        """
        clean_zip = self.validate_zip_code(zip_code)

        if not self.api_key:
            raise GeoapifyServiceError(
                "Geoapify API key is not configured in backend/.env. Please configure GEOAPIFY_API_KEY.",
                status_code=503,
            )

        params = {
            "postcode": clean_zip,
            "country": "United States",
            "filter": "countrycode:us",
            "type": "postcode",
            "apiKey": self.api_key,
        }

        try:
            if self.client:
                response = await self.client.get(self.GEOCODE_URL, params=params, timeout=10.0)
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.get(self.GEOCODE_URL, params=params, timeout=10.0)
        except httpx.RequestError as exc:
            raise GeoapifyServiceError(
                f"Network error while connecting to Geoapify Geocoding service: {str(exc)}",
                status_code=502,
            ) from exc

        if response.status_code in (401, 403):
            raise GeoapifyServiceError(
                "Geoapify API request was rejected (invalid or unauthorized API key).",
                status_code=502,
            )
        elif response.status_code != 200:
            raise GeoapifyServiceError(
                f"Geoapify Geocoding service returned HTTP {response.status_code}: {response.text}",
                status_code=502,
            )

        data = response.json()
        features = data.get("features", [])
        if not features:
            raise UnresolvedZipCodeError(
                f"ZIP code '{clean_zip}' could not be resolved to a valid U.S. postcode location."
            )

        # Inspect the primary result to ensure it establishes the requested U.S. ZIP code
        feature = features[0]
        props = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates", [])

        # Validate country is United States
        country_code = str(props.get("country_code", "")).lower()
        country_name = str(props.get("country", "")).lower()
        if country_code != "us" and "united states" not in country_name and "usa" not in country_name:
            raise UnresolvedZipCodeError(
                f"ZIP code '{clean_zip}' resolved to a non-U.S. location ({props.get('country')})."
            )

        # Validate postcode establishes the requested 5-digit ZIP code
        result_postcode = str(props.get("postcode", "")).strip()
        # Postcode may be '02138' or '02138-1234'
        if not result_postcode or not result_postcode.startswith(clean_zip):
            raise UnresolvedZipCodeError(
                f"Lookup for '{clean_zip}' did not establish the requested U.S. ZIP code (returned: '{result_postcode or 'unknown'}')."
            )

        # Extract coordinates
        lat = props.get("lat")
        lon = props.get("lon")
        if lat is None or lon is None:
            if len(coords) >= 2:
                lon, lat = coords[0], coords[1]
            else:
                raise UnresolvedZipCodeError(
                    f"No geographic coordinates returned for ZIP code '{clean_zip}'."
                )

        return SearchCenter(
            latitude=float(lat),
            longitude=float(lon),
            city=props.get("city") or props.get("municipality") or props.get("county"),
            state=props.get("state_code") or props.get("state"),
            postcode=clean_zip,
            country="United States",
            formatted=props.get("formatted"),
        )

    async def get_hotels_near_point(
        self,
        center: SearchCenter,
        shortlisted_ids: Optional[set[str]] = None,
        radius_meters: int = settings.DEFAULT_RADIUS_METERS,
    ) -> list[HotelPlace]:
        """
        Obtains hotels within the specified radius (default 5 km) of the search center.
        Search center is strictly the returned geocoded location.
        """
        if not self.api_key:
            raise GeoapifyServiceError(
                "Geoapify API key is not configured in backend/.env. Please configure GEOAPIFY_API_KEY.",
                status_code=503,
            )

        shortlisted = shortlisted_ids or set()
        params = {
            "categories": "accommodation.hotel,accommodation.motel",
            "filter": f"circle:{center.longitude},{center.latitude},{radius_meters}",
            "bias": f"proximity:{center.longitude},{center.latitude}",
            "limit": 50,
            "apiKey": self.api_key,
        }

        try:
            if self.client:
                response = await self.client.get(self.PLACES_URL, params=params, timeout=10.0)
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.get(self.PLACES_URL, params=params, timeout=10.0)
        except httpx.RequestError as exc:
            raise GeoapifyServiceError(
                f"Network error while connecting to Geoapify Places service: {str(exc)}",
                status_code=502,
            ) from exc

        if response.status_code in (401, 403):
            raise GeoapifyServiceError(
                "Geoapify Places API request was rejected (invalid or unauthorized API key).",
                status_code=502,
            )
        elif response.status_code != 200:
            raise GeoapifyServiceError(
                f"Geoapify Places service returned HTTP {response.status_code}: {response.text}",
                status_code=502,
            )

        data = response.json()
        features = data.get("features", [])
        hotels: list[HotelPlace] = []

        for feat in features:
            props = feat.get("properties", {})
            geom = feat.get("geometry", {})
            coords = geom.get("coordinates", [])

            lat = props.get("lat")
            lon = props.get("lon")
            if lat is None or lon is None:
                if len(coords) >= 2:
                    lon, lat = coords[0], coords[1]
                else:
                    continue  # Omit entries without coordinates

            lat = float(lat)
            lon = float(lon)

            # Distance in meters
            dist_m = props.get("distance")
            if dist_m is None:
                dist_m = calculate_haversine_meters(center.latitude, center.longitude, lat, lon)
            else:
                dist_m = float(dist_m)

            dist_km = round(dist_m / 1000.0, 2)

            place_id = props.get("place_id") or f"place_{lat:.5f}_{lon:.5f}"

            # Format categories honestly
            cats = props.get("categories", [])
            primary_cat = "Hotel"
            if "accommodation.motel" in cats:
                primary_cat = "Motel"
            elif "accommodation.hotel" in cats:
                primary_cat = "Hotel"
            elif cats:
                primary_cat = cats[0].replace("accommodation.", "").replace("_", " ").title()

            # Contacts / links if present
            contact = props.get("contact", {}) or {}
            website = props.get("website") or contact.get("website")
            phone = props.get("phone") or contact.get("phone")

            raw_name = props.get("name")
            name = raw_name.strip() if raw_name and raw_name.strip() else "Name not provided"

            formatted_address = props.get("formatted") or props.get("address_line2")

            hotel = HotelPlace(
                place_id=place_id,
                name=name,
                formatted_address=formatted_address,
                street=props.get("street") or props.get("address_line1"),
                city=props.get("city") or center.city,
                state=props.get("state_code") or props.get("state") or center.state,
                postcode=props.get("postcode"),
                latitude=lat,
                longitude=lon,
                distance_meters=dist_m,
                distance_km=dist_km,
                category=primary_cat,
                website=website,
                phone=phone,
                is_shortlisted=place_id in shortlisted,
            )
            hotels.append(hotel)

        # Sort hotels by distance from search center
        hotels.sort(key=lambda h: h.distance_meters if h.distance_meters is not None else 999999)
        return hotels

    async def search_hotels_by_zip(
        self,
        zip_code: str,
        shortlisted_ids: Optional[set[str]] = None,
    ) -> HotelSearchResponse:
        """
        Coordinates full workflow:
        1. Validate 5-digit ZIP code.
        2. Resolve to U.S. postcode location (search center).
        3. Query hotels within 5 km of that search center.
        """
        center = await self.geocode_us_zip(zip_code)
        hotels = await self.get_hotels_near_point(center, shortlisted_ids=shortlisted_ids)

        return HotelSearchResponse(
            zip_code=center.postcode,
            search_center=center,
            radius_km=round(settings.DEFAULT_RADIUS_METERS / 1000.0, 1),
            total=len(hotels),
            results=hotels,
        )


_service_instance: Optional[GeoapifyService] = None

def get_geoapify_service() -> GeoapifyService:
    global _service_instance
    if _service_instance is None:
        _service_instance = GeoapifyService()
    return _service_instance
