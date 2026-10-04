"""Testdaten-Seed für die lokale Entwicklung (Issue #468).

Ein neuer Worktree startet mit leerer Datenbank; ``./scripts/dev-server.sh`` spielt die
Testdaten ein. Seit der zentralen Passwortregel (#383) scheiterte das am Passwort
``admin``, der Worktree blieb ohne Admin und ohne Beispieldaten.
"""

from app.models.user import Role
from app.seed import TESTDATA_ADMIN_PASSWORD
from app.seed import seed_testdata
from app.services.auth_service import authenticate_user
from app.services.auth_service import create_user
from sqlmodel import Session


def test_seed_runs_on_an_empty_database(session: Session) -> None:
    result = seed_testdata(session)

    assert result["admin"] == 1
    assert result["items"] > 0


def test_documented_admin_can_log_in(session: Session) -> None:
    seed_testdata(session)

    assert authenticate_user(session, "admin", TESTDATA_ADMIN_PASSWORD).username == "admin"


def test_existing_admin_keeps_its_password(session: Session) -> None:
    """Der Seed ergänzt nur (#460): ein vorhandener Admin behält sein Passwort."""
    create_user(session, username="admin", email="admin@example.com", password="eigenes-passwort", role=Role.ADMIN)

    result = seed_testdata(session)

    assert result["admin"] == 0
    assert authenticate_user(session, "admin", "eigenes-passwort").username == "admin"
