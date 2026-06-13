"""Discovery engine: runs the rules-gate across the whole scheme catalog to build
the ranked 'entitlement graph' — including schemes the user didn't ask about —
and resolves dependency-chains (a scheme that needs a certificate that is itself
an application). See docs spec §3 (Discovery & impact).
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Optional

from ..schemas.core import (
    EligibilityResult,
    EligibilityStatus,
    Scheme,
)
from .facts import Fact
from .rules import DOC_FOR_PREREQUISITE_SCHEME, _PREREQUISITE_DOCS, evaluate_scheme


@dataclass
class DependencyNode:
    """A node in the dependency-chain: 'to get X you first need Y'."""
    scheme_id: str
    needs: list[str] = dc_field(default_factory=list)         # prerequisite scheme ids
    needs_documents: list[str] = dc_field(default_factory=list)


@dataclass
class EntitlementGraph:
    results: list[EligibilityResult]
    dependencies: list[DependencyNode]

    @property
    def qualifies(self) -> list[EligibilityResult]:
        return [r for r in self.results if r.status == EligibilityStatus.QUALIFIES]

    @property
    def surprises(self) -> list[EligibilityResult]:
        """Schemes the user did NOT ask about but qualifies for — the kicker."""
        return [
            r
            for r in self.results
            if not r.user_asked_for_it
            and r.status
            in (EligibilityStatus.QUALIFIES, EligibilityStatus.NEEDS_PREREQUISITE)
        ]


def run_discovery(
    schemes: list[Scheme],
    facts: dict[str, Fact],
    available_documents: set[str],
    asked_scheme_ids: Optional[set[str]] = None,
) -> EntitlementGraph:
    asked = asked_scheme_ids or set()
    results: list[EligibilityResult] = []
    deps: list[DependencyNode] = []

    by_id = {s.id: s for s in schemes}

    for scheme in schemes:
        res = evaluate_scheme(
            scheme,
            facts,
            available_documents,
            user_asked_for_it=scheme.id in asked,
        )
        results.append(res)

        if res.status == EligibilityStatus.NEEDS_PREREQUISITE:
            # Only unmet prerequisite schemes (their issued doc is still missing).
            needs_schemes = [
                sid for sid in scheme.prerequisite_schemes
                if DOC_FOR_PREREQUISITE_SCHEME.get(sid, "__none__") not in available_documents
            ]
            needs_docs = [
                d for d in scheme.requires_documents
                if d not in available_documents and d in _PREREQUISITE_DOCS
            ]
            # Link any missing prerequisite doc to the scheme that issues it.
            for doc in needs_docs:
                issuer = _doc_issuing_scheme(doc, by_id)
                if issuer and issuer not in needs_schemes:
                    needs_schemes.append(issuer)
            deps.append(
                DependencyNode(
                    scheme_id=scheme.id,
                    needs=needs_schemes,
                    needs_documents=needs_docs,
                )
            )

    results.sort(key=lambda r: r.score, reverse=True)
    return EntitlementGraph(results=results, dependencies=deps)


# Maps a prerequisite document to the scheme/cert that produces it.
_DOC_ISSUER = {
    "income_cert": "income-certificate",
    "caste_cert": "caste-certificate",
    "domicile_cert": "domicile-certificate",
    "disability_cert": "disability-certificate-udid",
}


def _doc_issuing_scheme(doc: str, by_id: dict[str, Scheme]) -> Optional[str]:
    sid = _DOC_ISSUER.get(doc)
    return sid if sid and sid in by_id else None
