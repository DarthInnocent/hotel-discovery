import pytest
import httpx
from unittest.mock import AsyncMock, patch

from app.services.geoapify_service import (
    GeoapifyService,
    InvalidZipCodeError,
    UnresolvedZipCodeError,
    GeoapifyServiceError,
    calculate_haversine_meters,
)
from app.schemas.hotel import SearchCenter

@pytest.mark.asyncio
async def test_geocode_success_matching_us_zip():
    # Mock Geoapify geocode response
    mock_payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "country_code": "us",
                    "country": "United States",
                    "postcode": "02138",
                    "city": "Cambridge",
                    "state": "Massachusetts",
                    "state_code": "MA",
                    "lat": 42.3736,
                    "lon": -71.1097,
                    "formatted": "Cambridge, MA 02138, United States",
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [-71.1097, 42.3736],
                },
            }
        ],
    }

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = httpx.Response(status_code=200, json=mock_payload, request=httpx.Request("GET", "https://api.geoapify.com"))
    mock_client.get.return_value = mock_response

    service = GeoapifyService(api_key="valid_key", client=mock_client)
    center = await service.geocode_us_zip("02138")

    assert center.postcode == "02138"
    assert center.city == "Cambridge"
    assert center.state == "MA"
    assert center.latitude == 42.3736
    assert center.longitude == -71.1097
    assert center.country == "United States"

@pytest.mark.asyncio
async def test_geocode_rejects_non_us_country():
    # Geoapify returns a non-US result (e.g. Germany or Mexico)
    mock_payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "country_code": "de",
                    "country": "Germany",
                    "postcode": "02138",
                    "city": "Some City",
                    "lat": 51.0,
                    "lon": 13.0,
                },
            }
        ],
    }

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = httpx.Response(200, json=mock_payload, request=httpx.Request("GET", "https://api.geoapify.com"))

    service = GeoapifyService(api_key="valid_key", client=mock_client)
    with pytest.raises(UnresolvedZipCodeError) as exc_info:
        await service.geocode_us_zip("02138")
    assert "non-U.S. location" in str(exc_info.value)

@pytest.mark.asyncio
async def test_geocode_rejects_mismatched_postcode_silent_redirect_prevention():
    # Requirement: "A lookup that does not establish the requested U.S. ZIP code must not silently become a different-location search."
    mock_payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "country_code": "us",
                    "country": "United States",
                    "postcode": "90211",  # Different ZIP returned by API
                    "city": "Beverly Hills",
                    "lat": 34.06,
                    "lon": -118.39,
                },
            }
        ],
    }

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = httpx.Response(200, json=mock_payload, request=httpx.Request("GET", "https://api.geoapify.com"))

    service = GeoapifyService(api_key="valid_key", client=mock_client)
    with pytest.raises(UnresolvedZipCodeError) as exc_info:
        await service.geocode_us_zip("90210")
    assert "did not establish the requested U.S. ZIP code" in str(exc_info.value)

@pytest.mark.asyncio
async def test_geocode_unresolved_when_empty_features():
    mock_payload = {"type": "FeatureCollection", "features": []}
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = httpx.Response(200, json=mock_payload, request=httpx.Request("GET", "https://api.geoapify.com"))

    service = GeoapifyService(api_key="valid_key", client=mock_client)
    with pytest.raises(UnresolvedZipCodeError) as exc_info:
        await service.geocode_us_zip("00000")
    assert "could not be resolved" in str(exc_info.value)

@pytest.mark.asyncio
async def test_geocode_service_failure_distinguished_from_empty_success():
    # Requirement: "It must not describe a service failure as an empty successful search."
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    # 401 Unauthorized
    mock_client.get.return_value = httpx.Response(401, text="Unauthorized", request=httpx.Request("GET", "https://api.geoapify.com"))

    service = GeoapifyService(api_key="invalid_key", client=mock_client)
    with pytest.raises(GeoapifyServiceError) as exc_info:
        await service.geocode_us_zip("90210")
    assert exc_info.value.status_code == 502
    assert "invalid or unauthorized" in str(exc_info.value).lower()

@pytest.mark.asyncio
async def test_places_search_hotels_and_honest_representation():
    center = SearchCenter(
        latitude=34.0736,
        longitude=-118.4004,
        city="Beverly Hills",
        state="CA",
        postcode="90210",
        country="United States",
        formatted="Beverly Hills, CA 90210",
    )

    mock_places_payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "place_id": "hotel_1",
                    "name": "The Beverly Hills Hotel",
                    "formatted": "9641 Sunset Blvd, Beverly Hills, CA 90210",
                    "street": "Sunset Blvd",
                    "city": "Beverly Hills",
                    "state_code": "CA",
                    "postcode": "90210",
                    "lat": 34.0815,
                    "lon": -118.4140,
                    "distance": 1500,
                    "categories": ["accommodation.hotel"],
                    "website": "https://www.dorchestercollection.com",
                    "phone": "+1 310-276-2251",
                },
                "geometry": {"type": "Point", "coordinates": [-118.4140, 34.0815]},
            },
            {
                "type": "Feature",
                "properties": {
                    "place_id": "hotel_2",
                    # Name is deliberately missing to test honest labeling
                    "name": None,
                    "formatted": "123 Wilshire Blvd, Beverly Hills, CA 90210",
                    "lat": 34.0670,
                    "lon": -118.3980,
                    "distance": 800,
                    "categories": ["accommodation.hotel"],
                },
                "geometry": {"type": "Point", "coordinates": [-118.3980, 34.0670]},
            },
        ],
    }

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = httpx.Response(200, json=mock_places_payload, request=httpx.Request("GET", "https://api.geoapify.com"))

    service = GeoapifyService(api_key="valid_key", client=mock_client)
    hotels = await service.get_hotels_near_point(center, shortlisted_ids={"hotel_1"})

    assert len(hotels) == 2
    # Verify distance sorting: hotel_2 (800m) should be before hotel_1 (1500m)
    assert hotels[0].place_id == "hotel_2"
    assert hotels[0].distance_meters == 800
    assert hotels[0].name == "Name not provided"  # Honest fallback
    assert hotels[0].is_shortlisted is False

    assert hotels[1].place_id == "hotel_1"
    assert hotels[1].name == "The Beverly Hills Hotel"
    assert hotels[1].distance_meters == 1500
    assert hotels[1].distance_km == 1.5
    assert hotels[1].is_shortlisted is True
    assert hotels[1].website == "https://www.dorchestercollection.com"

def test_haversine_calculation():
    # Distance between Beverly Hills and Santa Monica (~8-9km)
    dist = calculate_haversine_meters(34.0736, -118.4004, 34.0195, -118.4912)
    assert 8000 < dist < 12000
