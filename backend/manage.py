#!/usr/bin/env python3
"""Sahayak management CLI.

Usage:
    python backend/manage.py init-db        # create tables
    python backend/manage.py reset-db       # drop & recreate tables
    python backend/manage.py list-schemes   # list scheme ids from /shared
    python backend/manage.py stats          # KB + row counts
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _cmd_init_db(_: argparse.Namespace) -> None:
    from app.db import init_db

    init_db()
    print("init-db: tables created")


def _cmd_reset_db(_: argparse.Namespace) -> None:
    from app.db import Base, engine, init_db

    Base.metadata.drop_all(engine)
    init_db()
    print("reset-db: dropped & recreated all tables")


def _cmd_list_schemes(_: argparse.Namespace) -> None:
    from app.core.registry import load_schemes

    for s in load_schemes():
        print(f"{s.id:32} {s.category:14} {s.name.get('en', s.id)}")


def _cmd_stats(_: argparse.Namespace) -> None:
    from app.core.registry import load_form_templates, load_schemes
    from app.db import SessionLocal, SessionRow, TrackingRow

    with SessionLocal() as db:
        sessions = db.query(SessionRow).count()
        tracking = db.query(TrackingRow).count()
    print(
        f"schemes={len(load_schemes())} forms={len(load_form_templates())} "
        f"sessions={sessions} tracking={tracking}"
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="manage.py", description="Sahayak admin commands")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-db", help="create tables").set_defaults(fn=_cmd_init_db)
    sub.add_parser("reset-db", help="drop & recreate tables").set_defaults(fn=_cmd_reset_db)
    sub.add_parser("list-schemes", help="list scheme ids").set_defaults(fn=_cmd_list_schemes)
    sub.add_parser("stats", help="KB + row counts").set_defaults(fn=_cmd_stats)
    args = parser.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
