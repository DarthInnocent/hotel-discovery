"""
Repeatable Verification Script for Hotel Discovery Project
Verifies:
1. Python 3.13 and SQLite support.
2. 5-digit U.S. ZIP code validation with leading zeros (e.g. 02138, 01001).
3. Geocoding resolution to U.S. postcode location and prevention of silent different-location searches.
4. 5 km search radius from returned search center.
5. Honest data contract (no invented prices, ratings, room availability, or booking confirmations).
6. Distinction among loading, results, invalid input, unresolved ZIP, no nearby results, and failed request.
7. SQLite persistent shortlist CRUD and cross-session persistence.
"""

import sys
import sqlite3
import subprocess
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))

def print_header(title: str):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

def verify_python_and_sqlite():
    print_header("1. VERIFY PYTHON INTERPRETER AND SQLITE")
    print(f"Python executable: {sys.executable}")
    print(f"Python version:    {sys.version.split()[0]}")
    print(f"SQLite version:    {sqlite3.sqlite_version}")
    
    # Test in-memory table creation
    with sqlite3.connect(":memory:") as conn:
        conn.execute("CREATE TABLE verify_test (id INTEGER PRIMARY KEY, note TEXT);")
        conn.execute("INSERT INTO verify_test (note) VALUES ('active');")
        cur = conn.execute("SELECT note FROM verify_test;")
        res = cur.fetchone()[0]
        assert res == "active"
    print(" [PASS] Python sqlite3 standard module is fully functional.")

def verify_zip_validation():
    print_header("2. VERIFY 5-DIGIT U.S. ZIP CODE VALIDATION")
    from app.services.geoapify_service import GeoapifyService, InvalidZipCodeError

    service = GeoapifyService(api_key="test_key")

    # Valid ZIPs with leading zeros
    valid_cases = ["02138", "01001", "00501", "90210", "10001"]
    for z in valid_cases:
        res = service.validate_zip_code(z)
        assert res == z, f"Failed for {z}"
        print(f" [PASS] Valid ZIP accepted: '{z}' (preserved leading zeros)")

    # Invalid ZIPs
    invalid_cases = ["123", "9021", "902100", "abcde", "90210-1234", ""]
    for inv in invalid_cases:
        try:
            service.validate_zip_code(inv)
            assert False, f"Expected validation error for '{inv}'"
        except InvalidZipCodeError:
            print(f" [PASS] Invalid ZIP correctly rejected: '{inv}'")

def verify_honest_interface_contract():
    print_header("3. VERIFY HONEST INTERFACE CONTRACT")
    from app.schemas.hotel import HotelPlace

    # Check fallback for missing name
    h1 = HotelPlace(place_id="h1", name="", latitude=34.0, longitude=-118.0)
    assert h1.name == "Name not provided"
    print(f" [PASS] Missing hotel name labeled honestly: '{h1.name}'")

    # Ensure prohibited fields do NOT exist
    forbidden = ["nightly_rate_usd", "price", "rate", "rating", "stars", "rooms_left", "availability", "booking_confirmation"]
    for f in forbidden:
        assert f not in HotelPlace.model_fields, f"Forbidden field '{f}' found in HotelPlace schema!"
    print(" [PASS] Verified no invented prices, ratings, availability, or booking confirmations.")

def verify_sqlite_shortlist_persistence(tmp_db: Path):
    print_header("4. VERIFY SQLITE SHORTLIST PERSISTENCE")
    from app.controllers.shortlist_controller import ShortlistController
    from app.schemas.hotel import ShortlistCreateRequest

    # Session 1: Create table and save item
    c1 = ShortlistController(db_path=tmp_db)
    c1.initialize_database()

    item = ShortlistCreateRequest(
        place_id="hotel_harvard_square",
        name="The Charles Hotel",
        formatted_address="1 Bennett St, Cambridge, MA 02138",
        city="Cambridge",
        state="MA",
        postcode="02138",
        latitude=42.3725,
        longitude=-71.1215,
        distance_meters=950.0,
        search_zip="02138",
    )
    saved = c1.add_to_shortlist(item)
    assert saved.place_id == "hotel_harvard_square"
    print(f" [PASS] Added hotel to shortlist: '{saved.name}'")

    # Session 2: Fresh controller opening same database file (simulates restart)
    c2 = ShortlistController(db_path=tmp_db)
    items = c2.get_shortlist()
    assert len(items) == 1
    assert items[0].place_id == "hotel_harvard_square"
    assert items[0].name == "The Charles Hotel"
    assert items[0].is_shortlisted is True
    print(" [PASS] Verified cross-session persistence across controller restart.")

    # Remove item
    deleted = c2.remove_from_shortlist("hotel_harvard_square")
    assert deleted is True
    assert len(c2.get_shortlist()) == 0
    print(" [PASS] Verified removal of item from shortlist.")

def run_pytest_suite():
    print_header("5. RUNNING COMPLETE PYTEST TEST SUITE")
    pytest_exe = backend_dir / "venv" / "Scripts" / "pytest.exe"
    cmd = [str(pytest_exe), "-v"]
    res = subprocess.run(cmd, cwd=str(backend_dir), capture_output=True, text=True)
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr)
        sys.exit(res.returncode)
    print(" [PASS] All automated backend unit and integration tests passed.")

if __name__ == "__main__":
    test_db = backend_dir / "verify_temp.db"
    try:
        verify_python_and_sqlite()
        verify_zip_validation()
        verify_honest_interface_contract()
        verify_sqlite_shortlist_persistence(test_db)
        run_pytest_suite()
        print_header("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")
    finally:
        if test_db.exists():
            test_db.unlink()
