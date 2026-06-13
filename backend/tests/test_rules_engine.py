"""Tests for the deterministic rules-gate (app.engine.rules).

These guard the project's non-negotiable rule: eligibility is decided by typed
predicates, never an LLM. We test the comparison primitive directly and run every
real scheme through evaluate_scheme to ensure it always returns a valid status.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.registry import load_schemes  # noqa: E402
from app.engine.rules import _compare, evaluate_scheme  # noqa: E402
from app.schemas.core import EligibilityStatus, Op  # noqa: E402


def test_compare_operators():
    assert _compare(Op.GE, "60", "60") is True
    assert _compare(Op.GE, "50", "60") is False
    assert _compare(Op.LE, 5, 10) is True
    assert _compare(Op.EQ, "Yes", "yes") is True      # normalised, case-insensitive
    assert _compare(Op.NE, "a", "b") is True
    assert _compare(Op.IN, "a", ["a", "b"]) is True
    assert _compare(Op.IN, "z", ["a", "b"]) is False
    assert _compare(Op.EXISTS, "something", None) is True
    assert _compare(Op.EXISTS, "", None) is False


def test_unknown_fact_is_undecided():
    # A missing fact must yield None (undecided), never a guess.
    assert _compare(Op.GE, None, "60") is None
    assert _compare(Op.EQ, "", "x") is None


def test_every_scheme_evaluates_to_a_valid_status():
    schemes = load_schemes()
    assert schemes, "scheme KB should not be empty"
    for scheme in schemes:
        result = evaluate_scheme(scheme, facts={}, available_documents=set())
        assert result.status in set(EligibilityStatus)
        assert 0.0 <= result.score <= 1.5
        assert result.scheme_id == scheme.id
