"""Tests für Rate Limit Service - Progressive Verzögerung."""

from app.models.login_attempt import LoginAttempt
from app.services import rate_limit_service
from collections.abc import Generator
from datetime import datetime
from datetime import timedelta
from freezegun import freeze_time
import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import create_engine


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    """Create In-Memory SQLite session for tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


class TestGetDelaySeconds:
    """Tests für die Verzögerungsberechnung."""

    def test_no_delay_for_first_attempt(self) -> None:
        """Erster Versuch hat keine Verzögerung."""
        assert rate_limit_service.get_delay_seconds(0) == 0
        assert rate_limit_service.get_delay_seconds(1) == 0

    def test_exponential_delay(self) -> None:
        """Verzögerung steigt exponentiell."""
        assert rate_limit_service.get_delay_seconds(2) == 1
        assert rate_limit_service.get_delay_seconds(3) == 2
        assert rate_limit_service.get_delay_seconds(4) == 4
        assert rate_limit_service.get_delay_seconds(5) == 8
        assert rate_limit_service.get_delay_seconds(6) == 16
        assert rate_limit_service.get_delay_seconds(7) == 32

    def test_max_delay_cap(self) -> None:
        """Verzögerung ist auf MAX_DELAY_SECONDS begrenzt."""
        assert rate_limit_service.get_delay_seconds(8) == 60
        assert rate_limit_service.get_delay_seconds(10) == 60
        assert rate_limit_service.get_delay_seconds(100) == 60


class TestRecordFailedAttempt:
    """Tests für das Aufzeichnen von Fehlversuchen."""

    def test_first_failed_attempt_creates_record(self, session: Session) -> None:
        """Erster Fehlversuch erstellt neuen Eintrag."""
        ip = "192.168.1.100"

        fail_count = rate_limit_service.record_failed_attempt(session, ip)

        assert fail_count == 1
        attempt = rate_limit_service.get_login_attempt(session, ip)
        assert attempt is not None
        assert attempt.fail_count == 1

    def test_subsequent_attempts_increment_count(self, session: Session) -> None:
        """Weitere Fehlversuche erhöhen den Zähler."""
        ip = "192.168.1.100"

        rate_limit_service.record_failed_attempt(session, ip)
        rate_limit_service.record_failed_attempt(session, ip)
        fail_count = rate_limit_service.record_failed_attempt(session, ip)

        assert fail_count == 3
        attempt = rate_limit_service.get_login_attempt(session, ip)
        assert attempt is not None
        assert attempt.fail_count == 3

    def test_different_ips_tracked_separately(self, session: Session) -> None:
        """Verschiedene IPs werden separat getrackt."""
        ip1 = "192.168.1.100"
        ip2 = "192.168.1.101"

        rate_limit_service.record_failed_attempt(session, ip1)
        rate_limit_service.record_failed_attempt(session, ip1)
        rate_limit_service.record_failed_attempt(session, ip2)

        attempt1 = rate_limit_service.get_login_attempt(session, ip1)
        attempt2 = rate_limit_service.get_login_attempt(session, ip2)

        assert attempt1 is not None
        assert attempt1.fail_count == 2
        assert attempt2 is not None
        assert attempt2.fail_count == 1


class TestRecordSuccessfulLogin:
    """Tests für das Zurücksetzen nach erfolgreichem Login."""

    def test_successful_login_resets_count(self, session: Session) -> None:
        """Erfolgreicher Login setzt Zähler zurück."""
        ip = "192.168.1.100"

        rate_limit_service.record_failed_attempt(session, ip)
        rate_limit_service.record_failed_attempt(session, ip)
        rate_limit_service.record_failed_attempt(session, ip)

        rate_limit_service.record_successful_login(session, ip)

        attempt = rate_limit_service.get_login_attempt(session, ip)
        assert attempt is not None
        assert attempt.fail_count == 0

    def test_successful_login_for_unknown_ip(self, session: Session) -> None:
        """Erfolgreicher Login für unbekannte IP macht nichts."""
        ip = "192.168.1.100"

        # Should not raise
        rate_limit_service.record_successful_login(session, ip)

        attempt = rate_limit_service.get_login_attempt(session, ip)
        assert attempt is None


class TestGetRequiredDelay:
    """Tests für die Berechnung der erforderlichen Wartezeit."""

    def test_no_delay_for_new_ip(self, session: Session) -> None:
        """Neue IP hat keine Wartezeit."""
        delay = rate_limit_service.get_required_delay(session, "192.168.1.100")
        assert delay == 0

    def test_no_delay_after_first_failed_attempt(self, session: Session) -> None:
        """Nach erstem Fehlversuch keine Wartezeit."""
        ip = "192.168.1.100"
        rate_limit_service.record_failed_attempt(session, ip)

        delay = rate_limit_service.get_required_delay(session, ip)
        assert delay == 0

    def test_delay_after_multiple_failures(self, session: Session) -> None:
        """Nach mehreren Fehlversuchen gibt es Wartezeit."""
        ip = "192.168.1.100"

        # 3 Fehlversuche = 2 Sekunden Verzögerung
        rate_limit_service.record_failed_attempt(session, ip)
        rate_limit_service.record_failed_attempt(session, ip)
        rate_limit_service.record_failed_attempt(session, ip)

        delay = rate_limit_service.get_required_delay(session, ip)
        # Sollte ungefähr 2 Sekunden sein (könnte etwas weniger sein wegen Zeitablauf)
        assert delay <= 2

    def test_delay_resets_after_24_hours(self, session: Session) -> None:
        """Verzögerung wird nach 24h ohne Aktivität zurückgesetzt."""
        ip = "192.168.1.100"

        # Erstelle alten Eintrag
        attempt = LoginAttempt(
            ip_address=ip,
            fail_count=10,
            last_attempt=datetime.now() - timedelta(hours=25),
        )
        session.add(attempt)
        session.commit()

        # Sollte zurückgesetzt sein
        delay = rate_limit_service.get_required_delay(session, ip)
        assert delay == 0

        # Und der Zähler sollte resetted sein
        attempt = rate_limit_service.get_login_attempt(session, ip)
        assert attempt is not None
        assert attempt.fail_count == 0


class TestCleanupOldAttempts:
    """Tests für das Aufräumen alter Einträge."""

    def test_cleanup_removes_old_entries(self, session: Session) -> None:
        """Alte Einträge werden gelöscht."""
        # Erstelle alten Eintrag
        old_attempt = LoginAttempt(
            ip_address="192.168.1.100",
            fail_count=5,
            last_attempt=datetime.now() - timedelta(hours=25),
        )
        session.add(old_attempt)

        # Erstelle neuen Eintrag
        new_attempt = LoginAttempt(
            ip_address="192.168.1.101",
            fail_count=2,
            last_attempt=datetime.now(),
        )
        session.add(new_attempt)
        session.commit()

        # Cleanup
        deleted = rate_limit_service.cleanup_old_attempts(session)

        assert deleted == 1

        # Alter Eintrag weg, neuer noch da
        assert rate_limit_service.get_login_attempt(session, "192.168.1.100") is None
        assert rate_limit_service.get_login_attempt(session, "192.168.1.101") is not None

    def test_cleanup_with_no_old_entries(self, session: Session) -> None:
        """Cleanup ohne alte Einträge löscht nichts."""
        # Nur neuer Eintrag
        new_attempt = LoginAttempt(
            ip_address="192.168.1.100",
            fail_count=2,
            last_attempt=datetime.now(),
        )
        session.add(new_attempt)
        session.commit()

        deleted = rate_limit_service.cleanup_old_attempts(session)

        assert deleted == 0
        assert rate_limit_service.get_login_attempt(session, "192.168.1.100") is not None


class TestResetAfter24Hours:
    """Tests für das Reset-Verhalten nach 24 Stunden."""

    def test_failed_attempt_resets_after_24h(self, session: Session) -> None:
        """Fehlversuch resettet den Zähler wenn letzter Versuch > 24h her."""
        ip = "192.168.1.100"

        # Erstelle alten Eintrag mit vielen Fehlversuchen
        old_attempt = LoginAttempt(
            ip_address=ip,
            fail_count=10,
            last_attempt=datetime.now() - timedelta(hours=25),
        )
        session.add(old_attempt)
        session.commit()

        # Neuer Fehlversuch sollte bei 1 starten
        fail_count = rate_limit_service.record_failed_attempt(session, ip)
        assert fail_count == 1


class TestCeilRounding:
    """Tests für korrektes Aufrunden der Wartezeit."""

    @freeze_time("2025-01-15 12:00:00")
    def test_remaining_time_rounds_up_from_fraction(self, session: Session) -> None:
        """Verbleibende Zeit wird aufgerundet (0.5s -> 1s, nicht 0s).

        Regression-Test: int(0.5) = 0 würde Rate-Limiting umgehen.
        math.ceil(0.5) = 1 ist korrekt.
        """
        ip = "192.168.1.100"

        # Erstelle Eintrag: last_attempt war vor 1.5s, bei 3 Fails = 2s Verzögerung
        # -> remaining = 2s - 1.5s = 0.5s -> ceil(0.5) = 1
        attempt = LoginAttempt(
            ip_address=ip,
            fail_count=3,
            last_attempt=datetime(2025, 1, 15, 11, 59, 58, 500000),  # 1.5s ago
        )
        session.add(attempt)
        session.commit()

        delay = rate_limit_service.get_required_delay(session, ip)

        # Mit int() wäre das 0, mit ceil() ist es 1
        assert delay == 1

    @freeze_time("2025-01-15 12:00:00")
    def test_remaining_time_rounds_up_near_zero(self, session: Session) -> None:
        """Auch 0.1s verbleibend wird auf 1s aufgerundet."""
        ip = "192.168.1.100"

        # last_attempt vor 1.9s, bei 3 Fails = 2s Verzögerung
        # -> remaining = 0.1s -> ceil(0.1) = 1
        attempt = LoginAttempt(
            ip_address=ip,
            fail_count=3,
            last_attempt=datetime(2025, 1, 15, 11, 59, 58, 100000),  # 1.9s ago
        )
        session.add(attempt)
        session.commit()

        delay = rate_limit_service.get_required_delay(session, ip)

        # Mit int() wäre das 0, mit ceil() ist es 1
        assert delay == 1

    @freeze_time("2025-01-15 12:00:00")
    def test_exactly_expired_returns_zero(self, session: Session) -> None:
        """Genau abgelaufene Wartezeit gibt 0 zurück."""
        ip = "192.168.1.100"

        # last_attempt vor genau 2s, bei 3 Fails = 2s Verzögerung
        # -> remaining = 0s -> max(0, ceil(0)) = 0
        attempt = LoginAttempt(
            ip_address=ip,
            fail_count=3,
            last_attempt=datetime(2025, 1, 15, 11, 59, 58),  # exactly 2s ago
        )
        session.add(attempt)
        session.commit()

        delay = rate_limit_service.get_required_delay(session, ip)
        assert delay == 0

    @freeze_time("2025-01-15 12:00:00")
    def test_long_expired_returns_zero(self, session: Session) -> None:
        """Lange abgelaufene Wartezeit gibt 0 zurück (nicht negativ)."""
        ip = "192.168.1.100"

        # last_attempt vor 10s, bei 3 Fails = 2s Verzögerung
        # -> remaining = -8s -> max(0, ceil(-8)) = 0
        attempt = LoginAttempt(
            ip_address=ip,
            fail_count=3,
            last_attempt=datetime(2025, 1, 15, 11, 59, 50),  # 10s ago
        )
        session.add(attempt)
        session.commit()

        delay = rate_limit_service.get_required_delay(session, ip)
        assert delay == 0
