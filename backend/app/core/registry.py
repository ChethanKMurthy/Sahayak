"""Loads the scheme knowledge base and form-template DSL from /shared JSON.

Forms are data, not code: adding a scheme/form means dropping a JSON file in
/shared — no redeploy. Loaded once and cached.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from ..config import SHARED_DIR
from ..schemas.core import FormTemplate, Scheme


def _load_json_dir(path: Path) -> list[dict]:
    items: list[dict] = []
    if not path.exists():
        return items
    for f in sorted(path.glob("*.json")):
        with f.open(encoding="utf-8") as fh:
            data = json.load(fh)
            items.extend(data if isinstance(data, list) else [data])
    return items


@lru_cache
def load_schemes() -> list[Scheme]:
    return [Scheme(**d) for d in _load_json_dir(SHARED_DIR / "schemes")]


@lru_cache
def load_form_templates() -> list[FormTemplate]:
    return [FormTemplate(**d) for d in _load_json_dir(SHARED_DIR / "forms")]


def scheme_by_id(scheme_id: str) -> Scheme | None:
    return next((s for s in load_schemes() if s.id == scheme_id), None)


def form_by_id(form_id: str) -> FormTemplate | None:
    return next((f for f in load_form_templates() if f.id == form_id), None)


def form_for_scheme(scheme_id: str) -> FormTemplate | None:
    return next((f for f in load_form_templates() if f.scheme_id == scheme_id), None)


@lru_cache
def load_i18n() -> dict[str, dict[str, str]]:
    path = SHARED_DIR / "i18n" / "strings.json"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)
