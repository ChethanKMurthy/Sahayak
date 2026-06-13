"""Thin convenience wrappers over the registry for the orchestrator."""
from __future__ import annotations

from ..schemas.core import FormTemplate, Scheme
from .registry import (  # noqa: F401 re-export
    form_by_id,
    form_for_scheme,
    load_form_templates,
    load_schemes,
    scheme_by_id,
)


def all_schemes() -> list[Scheme]:
    return load_schemes()


def scheme_for(scheme_id: str) -> Scheme | None:
    return scheme_by_id(scheme_id)


def form_for(form_id: str) -> FormTemplate | None:
    return form_by_id(form_id)


def form_or_scheme_form(scheme_id: str) -> FormTemplate | None:
    """Accept either a scheme id or a form id and return the form template.

    Resolution order: the scheme's explicit form_template_id (so several schemes
    can share one form, e.g. the NSAP pensions) → form whose scheme_id matches →
    a form with this id directly.
    """
    scheme = scheme_by_id(scheme_id)
    if scheme and scheme.form_template_id:
        f = form_by_id(scheme.form_template_id)
        if f:
            return f
    return form_for_scheme(scheme_id) or form_by_id(scheme_id)
