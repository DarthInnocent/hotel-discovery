import pytest
from app.services.geoapify_service import GeoapifyService, InvalidZipCodeError

def test_valid_five_digit_zip_codes():
    service = GeoapifyService(api_key="dummy_key")
    
    # Valid ZIPs including leading zeros
    assert service.validate_zip_code("90210") == "90210"
    assert service.validate_zip_code("02138") == "02138"  # Cambridge, MA
    assert service.validate_zip_code("01001") == "01001"  # Agawam, MA
    assert service.validate_zip_code("00501") == "00501"  # Holtsville, NY
    assert service.validate_zip_code("  90210  ") == "90210"  # Trim whitespace

def test_invalid_zip_codes_raise_error():
    service = GeoapifyService(api_key="dummy_key")

    invalid_zips = [
        "",
        "   ",
        "1234",          # Too short
        "123",
        "902100",        # Too long
        "90210-1234",    # ZIP+4 is not accepted by requirement (5 digits)
        "abcde",         # Non-digits
        "9021a",         # Partial alpha
        "90 10",         # Contains spaces
        "-9021",         # Negative
        "9021.0",        # Float string
    ]

    for inv in invalid_zips:
        with pytest.raises(InvalidZipCodeError) as exc_info:
            service.validate_zip_code(inv)
        assert "5 numeric digits" in str(exc_info.value) or "enter a 5-digit" in str(exc_info.value)
