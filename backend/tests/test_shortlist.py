import pytest
from pathlib import Path
from app.controllers.shortlist_controller import ShortlistController
from app.schemas.hotel import ShortlistCreateRequest

def test_shortlist_crud_and_persistence(temp_db_path: Path):
    # Initialize first controller instance
    controller_1 = ShortlistController(db_path=temp_db_path)
    controller_1.initialize_database()

    # Initially empty
    assert len(controller_1.get_shortlist()) == 0
    assert len(controller_1.get_shortlisted_ids()) == 0

    # Add item
    item_1 = ShortlistCreateRequest(
        place_id="hotel_001",
        name="Harbor Lantern Hotel",
        formatted_address="100 Harbor Way, Boston, MA 02110",
        street="100 Harbor Way",
        city="Boston",
        state="MA",
        postcode="02110",
        latitude=42.355,
        longitude=-71.050,
        distance_meters=1250,
        category="Hotel",
        website="https://harborlantern.example.com",
        phone="+1 617-555-0199",
        search_zip="02110",
    )
    saved = controller_1.add_to_shortlist(item_1)
    assert saved.place_id == "hotel_001"
    assert saved.name == "Harbor Lantern Hotel"
    assert saved.is_shortlisted is True
    assert saved.distance_km == 1.25

    # Check existence
    assert "hotel_001" in controller_1.get_shortlisted_ids()
    shortlist = controller_1.get_shortlist()
    assert len(shortlist) == 1
    assert shortlist[0].place_id == "hotel_001"
    assert shortlist[0].name == "Harbor Lantern Hotel"

    # Add second item
    item_2 = ShortlistCreateRequest(
        place_id="hotel_002",
        name="Maple Square Inn",
        latitude=42.360,
        longitude=-71.060,
        distance_meters=2100,
    )
    controller_1.add_to_shortlist(item_2)
    assert len(controller_1.get_shortlist()) == 2

    # Simulate application restart with a NEW controller instance pointing to the same file
    controller_2 = ShortlistController(db_path=temp_db_path)
    persisted_items = controller_2.get_shortlist()
    assert len(persisted_items) == 2
    # Verify order is descending by saved_at (most recent first)
    assert persisted_items[0].place_id == "hotel_002"
    assert persisted_items[1].place_id == "hotel_001"

    # Delete item_1
    deleted = controller_2.remove_from_shortlist("hotel_001")
    assert deleted is True
    assert "hotel_001" not in controller_2.get_shortlisted_ids()
    assert len(controller_2.get_shortlist()) == 1

    # Deleting non-existent item returns False
    assert controller_2.remove_from_shortlist("non_existent") is False
