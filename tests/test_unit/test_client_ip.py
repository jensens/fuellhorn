"""Unit Tests: Client-IP-Auflösung für das Login-Rate-Limiting (Issue #364).

``resolve_client_ip`` ist eine reine Funktion aus Peer-IP, X-Forwarded-For-Header
und der Menge vertrauenswürdiger Proxys. X-Forwarded-For ist frei setzbar und darf
nur zählen, wenn der direkte Peer ein konfigurierter Proxy ist.
"""

from app.ui.auth import resolve_client_ip


def test_peer_ip_without_header() -> None:
    """Ohne X-Forwarded-For zählt die Peer-IP."""
    assert resolve_client_ip("198.51.100.7", None, frozenset()) == "198.51.100.7"


def test_forwarded_for_is_ignored_when_peer_is_not_trusted() -> None:
    """Ein direkter Client kann sich nicht per X-Forwarded-For eine andere IP geben."""
    assert resolve_client_ip("198.51.100.7", "203.0.113.5", frozenset()) == "198.51.100.7"


def test_forwarded_for_first_entry_is_used_behind_trusted_proxy() -> None:
    """Hinter einem vertrauenswürdigen Proxy zählt der erste Eintrag der Kette."""
    assert resolve_client_ip("10.0.0.1", "203.0.113.5, 10.0.0.1", frozenset({"10.0.0.1"})) == "203.0.113.5"


def test_empty_forwarded_for_behind_trusted_proxy_falls_back_to_peer() -> None:
    """Leerer Header hinter vertrauenswürdigem Proxy → Peer-IP."""
    assert resolve_client_ip("10.0.0.1", " , ", frozenset({"10.0.0.1"})) == "10.0.0.1"


def test_missing_peer_is_unknown() -> None:
    """Ohne Peer-Information (sollte nicht vorkommen) ein stabiler Platzhalter."""
    assert resolve_client_ip(None, None, frozenset()) == "unknown"
