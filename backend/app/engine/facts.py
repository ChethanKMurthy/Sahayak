"""Fact resolution: turn the collected FieldValues into a flat, typed fact map
that the rules-gate can evaluate, including derived facts like age-from-DOB.

A "fact" is a plain typed value plus the FieldValue it came from (for provenance).
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any, Optional

from dateutil import parser as dateparser
from dateutil.relativedelta import relativedelta

from ..schemas.core import FieldValue


@dataclass
class Fact:
    key: str
    value: Any
    source: Optional[FieldValue] = None
    derived: bool = False


def _parse_date(value: Any) -> Optional[dt.date]:
    if value in (None, ""):
        return None
    if isinstance(value, dt.date):
        return value
    try:
        return dateparser.parse(str(value), dayfirst=True).date()
    except (ValueError, OverflowError, TypeError):
        return None


def _to_number(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = "".join(c for c in str(value) if c.isdigit() or c in ".-")
    try:
        return float(cleaned) if cleaned not in ("", "-", ".") else None
    except ValueError:
        return None


# As-of date is injectable so the engine is deterministic and testable.
def build_fact_map(
    field_values: list[FieldValue], today: Optional[dt.date] = None
) -> dict[str, Fact]:
    """Build the fact map the rules-gate reads, adding derived facts."""
    today = today or dt.date.today()
    facts: dict[str, Fact] = {}

    for fv in field_values:
        facts[fv.key] = Fact(key=fv.key, value=fv.value, source=fv)

    # Derived: age from date of birth.
    if "dob" in facts and "age" not in facts:
        d = _parse_date(facts["dob"].value)
        if d:
            age = relativedelta(today, d).years
            facts["age"] = Fact(key="age", value=age, source=facts["dob"].source, derived=True)

    # Derived: numeric income from a possibly-formatted income string.
    if "income" in facts:
        n = _to_number(facts["income"].value)
        if n is not None:
            facts["income"] = Fact(key="income", value=n, source=facts["income"].source)

    if "annual_income" in facts and "income" not in facts:
        n = _to_number(facts["annual_income"].value)
        if n is not None:
            facts["income"] = Fact(
                key="income", value=n, source=facts["annual_income"].source, derived=True
            )

    # Derived: disability percent numeric.
    if "disability_percent" in facts:
        n = _to_number(facts["disability_percent"].value)
        if n is not None:
            facts["disability_percent"].value = n

    return facts
