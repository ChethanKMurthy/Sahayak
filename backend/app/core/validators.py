"""Validation helpers for Indian identity & banking fields.

Pure, dependency-free functions used to sanity-check user/OCR input before it
reaches the deterministic rules-gate. None of these make network calls or decide
eligibility — they only judge well-formedness.
"""
from __future__ import annotations

import re

__all__ = [
    "is_valid_aadhaar",
    "is_valid_ifsc",
    "is_valid_indian_phone",
    "normalize_phone",
]

# Verhoeff checksum tables — UIDAI uses Verhoeff for the 12th Aadhaar digit.
_MULT = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]
_PERM = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]


def _verhoeff_ok(number: str) -> bool:
    check = 0
    for i, digit in enumerate(reversed(number)):
        check = _MULT[check][_PERM[i % 8][int(digit)]]
    return check == 0


def is_valid_aadhaar(value: str) -> bool:
    """True if `value` is 12 digits (first digit 2-9) with a valid Verhoeff checksum."""
    s = re.sub(r"\s+", "", value or "")
    if not re.fullmatch(r"[2-9]\d{11}", s):
        return False
    return _verhoeff_ok(s)


_IFSC_RE = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")


def is_valid_ifsc(value: str) -> bool:
    """True if `value` matches the RBI IFSC format: 4 letters, a 0, then 6 alphanumerics."""
    return bool(_IFSC_RE.fullmatch((value or "").strip().upper()))


def normalize_phone(value: str) -> str:
    """Strip non-digits and a leading +91 / 0, returning the 10-digit core (best effort)."""
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    return digits


def is_valid_indian_phone(value: str) -> bool:
    """True if `value` normalizes to a 10-digit mobile number starting with 6-9."""
    return bool(re.fullmatch(r"[6-9]\d{9}", normalize_phone(value)))
