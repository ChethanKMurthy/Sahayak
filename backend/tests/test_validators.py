"""Unit tests for app.core.validators."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.validators import (  # noqa: E402
    is_valid_aadhaar,
    is_valid_ifsc,
    is_valid_indian_phone,
    normalize_phone,
)


def _make_valid_aadhaar(prefix11: str = "23412341234") -> str:
    """Find the one check digit that makes a valid Verhoeff Aadhaar for the prefix."""
    for d in "0123456789":
        candidate = prefix11 + d
        if is_valid_aadhaar(candidate):
            return candidate
    raise AssertionError("no valid Verhoeff check digit found")


def test_aadhaar_valid_and_invalid():
    valid = _make_valid_aadhaar()
    assert is_valid_aadhaar(valid)
    assert is_valid_aadhaar(f"{valid[:4]} {valid[4:8]} {valid[8:]}")  # spaced form
    # Flipping the last digit must break the checksum.
    wrong = valid[:-1] + str((int(valid[-1]) + 1) % 10)
    assert not is_valid_aadhaar(wrong)
    assert not is_valid_aadhaar("1234")            # too short
    assert not is_valid_aadhaar("1" + valid[1:])   # first digit < 2


def test_ifsc():
    assert is_valid_ifsc("HDFC0001234")
    assert is_valid_ifsc("karb0000234")   # lower-cased input is normalised
    assert not is_valid_ifsc("HDFC1001234")  # 5th char must be 0
    assert not is_valid_ifsc("HD0001234")    # too short


def test_phone():
    assert is_valid_indian_phone("9876543210")
    assert is_valid_indian_phone("+91 98765 43210")
    assert is_valid_indian_phone("098765-43210")
    assert not is_valid_indian_phone("1234567890")  # must start 6-9
    assert not is_valid_indian_phone("98765")
    assert normalize_phone("+91-98765 43210") == "9876543210"
