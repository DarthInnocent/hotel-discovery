import pytest
from app.schemas.hotel import HotelPlace, HotelSearchResponse, SearchCenter

def test_honest_data_contract_no_invented_fields():
    """
    Verification of prompt specification:
    'Available names, locations, and coordinates must correspond to the response;
     missing fields require an honest label or omission.
     No invented prices, ratings, room availability, or booking confirmations are permitted.'
    """
    hotel = HotelPlace(
        place_id="sample_hotel_001",
        name="",  # Missing name
        latitude=34.0522,
        longitude=-118.2437,
    )

    # Name is honestly reported as 'Name not provided'
    assert hotel.name == "Name not provided"
    assert hotel.formatted_address is None
    assert hotel.website is None
    assert hotel.phone is None

    # Verify that schema does NOT even have fields for fake prices, ratings, availability, or bookings
    model_fields = HotelPlace.model_fields.keys()
    forbidden_terms = ["price", "rate", "cost", "rating", "stars", "review", "rooms_left", "availability", "booking_confirmation"]
    for term in forbidden_terms:
        assert term not in model_fields, f"Forbidden invented field '{term}' found in HotelPlace model!"

    # Verify serialized dictionary contains only honest response fields
    data = hotel.model_dump()
    for term in forbidden_terms:
        assert term not in data, f"Forbidden invented field '{term}' found in serialized data!"
