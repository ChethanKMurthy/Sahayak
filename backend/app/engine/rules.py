"""The deterministic rules-gate.

This is the ONLY component allowed to output "you qualify." It evaluates each
scheme's hard criteria as typed predicates over the fact map — no LLM involved.
The LLM is later handed the *result* and asked only to phrase the human "why".

See docs/ARCHITECTURE.md §4.
"""
from __future__ import annotations

from typing import Any, Optional

from ..schemas.core import (
    Criterion,
    CriterionResult,
    EligibilityResult,
    EligibilityStatus,
    Op,
    Scheme,
)
from .facts import Fact


def _compare(op: Op, actual: Any, expected: Any) -> Optional[bool]:
    """Evaluate one predicate. Returns None when the fact is unknown."""
    if op in (Op.EXISTS,):
        return actual is not None and actual != ""
    if actual is None or actual == "":
        return None  # unknown — cannot decide this criterion yet

    try:
        if op == Op.GE:
            return float(actual) >= float(expected)
        if op == Op.LE:
            return float(actual) <= float(expected)
        if op == Op.GT:
            return float(actual) > float(expected)
        if op == Op.LT:
            return float(actual) < float(expected)
        if op == Op.EQ:
            return _norm(actual) == _norm(expected)
        if op == Op.NE:
            return _norm(actual) != _norm(expected)
        if op == Op.IN:
            return _norm(actual) in [_norm(v) for v in expected]
        if op == Op.NOT_IN:
            return _norm(actual) not in [_norm(v) for v in expected]
        if op == Op.TRUE:
            return bool(actual) is True
    except (ValueError, TypeError):
        return None
    return None


def _norm(v: Any) -> Any:
    return v.strip().lower() if isinstance(v, str) else v


def evaluate_criterion(crit: Criterion, facts: dict[str, Fact]) -> CriterionResult:
    fact = facts.get(crit.field)
    actual = fact.value if fact else None
    passed = _compare(crit.op, actual, crit.value)
    return CriterionResult(criterion=crit, passed=passed, actual=actual)


def evaluate_scheme(
    scheme: Scheme,
    facts: dict[str, Fact],
    available_documents: set[str],
    user_asked_for_it: bool = False,
) -> EligibilityResult:
    """Deterministically decide a single scheme.

    A prerequisite scheme is 'unmet' only when the document it issues is missing —
    if the user already has the income/caste certificate, the prerequisite is
    satisfied even though it is listed. Unmet prerequisites dominate the status
    (NEEDS_PREREQUISITE) because the missing facts will come from those very certs.
    """
    results = [evaluate_criterion(c, facts) for c in scheme.criteria]

    failed = [r for r in results if r.passed is False]
    unknown = [r for r in results if r.passed is None]
    passed = [r for r in results if r.passed is True]

    # Which declared prerequisite schemes are unmet (their issued doc is missing)?
    unmet_prereq_schemes = [
        sid for sid in scheme.prerequisite_schemes
        if DOC_FOR_PREREQUISITE_SCHEME.get(sid, "__none__") not in available_documents
    ]
    # Prerequisite-type required documents that are missing and not already covered.
    missing_prereq_docs = [
        d for d in scheme.requires_documents
        if d in _PREREQUISITE_DOCS and d not in available_documents
    ]
    has_unmet_prereq = bool(unmet_prereq_schemes or missing_prereq_docs)

    if failed:
        status = EligibilityStatus.DOES_NOT_QUALIFY
    elif has_unmet_prereq:
        status = EligibilityStatus.NEEDS_PREREQUISITE
    elif unknown:
        status = EligibilityStatus.NEEDS_INFO
    else:
        status = EligibilityStatus.QUALIFIES

    total = max(len(scheme.criteria), 1)
    base = {
        EligibilityStatus.QUALIFIES: 1.0,
        EligibilityStatus.NEEDS_PREREQUISITE: 0.7,
        EligibilityStatus.NEEDS_INFO: 0.4,
        EligibilityStatus.DOES_NOT_QUALIFY: 0.0,
    }[status]
    score = base + 0.01 * len(passed) / total
    if user_asked_for_it:
        score += 0.0001

    return EligibilityResult(
        scheme_id=scheme.id,
        status=status,
        score=round(score, 4),
        criterion_results=results,
        missing_facts=[r.criterion.field for r in unknown],
        missing_prerequisites=missing_prereq_docs + [f"scheme:{s}" for s in unmet_prereq_schemes],
        user_asked_for_it=user_asked_for_it,
    )


# Documents that are themselves applications → trigger dependency-chain detection.
_PREREQUISITE_DOCS = {
    "income_cert",
    "caste_cert",
    "domicile_cert",
    "disability_cert",
}

# The document each prerequisite scheme issues (so we know when it's satisfied).
DOC_FOR_PREREQUISITE_SCHEME = {
    "income-certificate": "income_cert",
    "caste-certificate": "caste_cert",
    "domicile-certificate": "domicile_cert",
    "disability-certificate-udid": "disability_cert",
}
