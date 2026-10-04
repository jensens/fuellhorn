"""Einheitliche Mengenformatierung für Karte, Bottom-Sheet und Benachrichtigungen (Issue #365)."""

from ...services.item_service import QUANTITY_DECIMALS
from ...services.item_service import normalize_quantity


def format_quantity(value: float, unit: str | None = None) -> str:
    """Formatiert eine Menge ohne Float-Rauschen und ohne überflüssige Nullen.

    500.0 → "500", 0.5 → "0.5", 0.1 + 0.2 → "0.3", 5.55e-17 → "0".
    Mit ``unit`` wird die Einheit angehängt: "2.5 kg".
    """
    normalized = normalize_quantity(value)
    if normalized == int(normalized):
        text = str(int(normalized))
    else:
        text = f"{normalized:.{QUANTITY_DECIMALS}f}".rstrip("0").rstrip(".")
    return f"{text} {unit}" if unit else text
