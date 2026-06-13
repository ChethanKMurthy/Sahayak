"""Tests for DbStorage — PDFs round-trip through the database, not the filesystem."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Point the engine at a throwaway SQLite file BEFORE importing app.db.
_TMP = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_TMP.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP.name}"

from app.db import init_db  # noqa: E402
from app.services.storage import DbStorage  # noqa: E402


def setup_module(_module):
    init_db()


def test_pdf_round_trip():
    store = DbStorage()
    data = b"%PDF-1.4 hello sahayak"
    url = store.put_pdf("s_test/form.pdf", data)
    assert url == "/api/files/s_test/form.pdf"
    assert store.get_pdf("s_test/form.pdf") == data


def test_overwrite_same_key():
    store = DbStorage()
    store.put_pdf("s_test/dup.pdf", b"first")
    store.put_pdf("s_test/dup.pdf", b"second")
    assert store.get_pdf("s_test/dup.pdf") == b"second"


def test_missing_returns_none():
    assert DbStorage().get_pdf("does/not-exist.pdf") is None


def teardown_module(_module):
    try:
        os.unlink(_TMP.name)
    except OSError:
        pass
