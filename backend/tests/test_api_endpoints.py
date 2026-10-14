import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from main import app
from app.services.geoapify_service import (
    GeoapifyService,
    get_geoapify_service,
    InvalidZipCodeError,
    UnresolvedZipCodeError,
    GeoapifyServiceError,
)
from app.schemas.hotel import SearchCenter, HotelPlace, HotelSearchResponse

def test_health_check(test_client: TestClient):
    response = test_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data

def test_search_invalid_zip_code(test_client: TestClient):
    response = test_client.get("/api/hotels/search?zip_code=123")
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error_type"] == "invalid_input"
    assert "5 numeric digits" in data["detail"]["message"]

def test_search_unresolved_zip_code(test_client: TestClient):
    mock_service = AsyncMock(spec=GeoapifyService)
    mock_service.search_hotels_by_zip.side_effect = UnresolvedZipCodeError("Could not resolve ZIP code '00000'")
    
    app.dependency_overrides[get_geoapify_service] = lambda: mock_service
    try:
        response = test_client.get("/api/hotels/search?zip_code=00000")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error_type"] == "unresolved_zip"
        assert "Could not resolve" in data["detail"]["message"]
    finally:
        app.dependency_overrides.pop(get_geoapify_service, None)

def test_search_service_failure(test_client: TestClient):
    # Requirement: "It must not describe a service failure as an empty successful search."
    mock_service = AsyncMock(spec=GeoapifyService)
    mock_service.search_hotels_by_zip.side_effect = GeoapifyServiceError("Geoapify API rate limit exceeded", status_code=502)

    app.dependency_overrides[get_geoapify_service] = lambda: mock_service
    try:
        response = test_client.get("/api/hotels/search?zip_code=90210")
        assert response.status_code == 502
        data = response.json()
        assert data["detail"]["error_type"] == "service_failure"
        assert "rate limit exceeded" in data["detail"]["message"]
    finally:
        app.dependency_overrides.pop(get_geoapify_service, None)

def test_search_successful_empty_results(test_client: TestClient):
    # Valid resolved ZIP with 0 hotels nearby (different from service error)
    center = SearchCenter(
        latitude=39.0,
        longitude=-105.0,
        city="Remote Town",
        state="CO",
        postcode="80456",
        country="United States",
        formatted="Remote Town, CO 80456",
    )
    mock_result = HotelSearchResponse(
        zip_code="80456",
        search_center=center,
        radius_km=5.0,
        total=0,
        results=[],
    )

    mock_service = AsyncMock(spec=GeoapifyService)
    mock_service.search_hotels_by_zip.return_value = mock_result

    app.dependency_overrides[get_geoapify_service] = lambda: mock_service
    try:
        response = test_client.get("/api/hotels/search?zip_code=80456")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["results"] == []
        assert data["search_center"]["postcode"] == "80456"
    finally:
        app.dependency_overrides.pop(get_geoapify_service, None)

def test_search_successful_with_hotels(test_client: TestClient):
    center = SearchCenter(
        latitude=42.3736,
        longitude=-71.1097,
        city="Cambridge",
        state="MA",
        postcode="02138",
        country="United States",
        formatted="Cambridge, MA 02138",
    )
    hotel = HotelPlace(
        place_id="hotel_harvard_sq",
        name="The Charles Hotel",
        formatted_address="1 Bennett St, Cambridge, MA 02138",
        city="Cambridge",
        state="MA",
        postcode="02138",
        latitude=42.3725,
        longitude=-71.1215,
        distance_meters=950.0,
        distance_km=0.95,
        category="Hotel",
    )
    mock_result = HotelSearchResponse(
        zip_code="02138",
        search_center=center,
        radius_km=5.0,
        total=1,
        results=[hotel],
    )

    mock_service = AsyncMock(spec=GeoapifyService)
    mock_service.search_hotels_by_zip.return_value = mock_result

    app.dependency_overrides[get_geoapify_service] = lambda: mock_service
    try:
        response = test_client.get("/api/hotels/search?zip_code=02138")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["zip_code"] == "02138"  # Leading zero preserved
        assert data["results"][0]["name"] == "The Charles Hotel"
        assert data["results"][0]["distance_km"] == 0.95
    finally:
        app.dependency_overrides.pop(get_geoapify_service, None)

def test_shortlist_endpoints(test_client: TestClient):
    # GET shortlist initially empty
    resp = test_client.get("/api/shortlist")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0

    # POST add item
    payload = {
        "place_id": "hotel_999",
        "name": "Ocean View Lodge",
        "formatted_address": "500 Shoreline Dr, Long Beach, CA 90802",
        "city": "Long Beach",
        "state": "CA",
        "postcode": "90802",
        "latitude": 33.76,
        "longitude": -118.19,
        "distance_meters": 1400.0,
        "category": "Hotel",
        "search_zip": "90802",
    }
    create_resp = test_client.post("/api/shortlist", json=payload)
    assert create_resp.status_code == 201
    assert create_resp.json()["place_id"] == "hotel_999"
    assert create_resp.json()["is_shortlisted"] is True

    # Verify in GET shortlist
    get_resp = test_client.get("/api/shortlist")
    assert get_resp.status_code == 200
    assert get_resp.json()["total"] == 1
    assert get_resp.json()["shortlist"][0]["name"] == "Ocean View Lodge"

    # DELETE item
    del_resp = test_client.delete("/api/shortlist/hotel_999")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "deleted"

    # DELETE non-existent item returns 404
    del_404 = test_client.delete("/api/shortlist/hotel_999")
    assert del_404.status_code == 404
