"""Sentinel für optionale Service-Parameter: „nicht übergeben“ vs. „auf None setzen“ (Issues #386, #395)."""


class Unset:
    """Feld wurde nicht übergeben; unterscheidet sich von ``None`` (= Feld leeren)."""

    def __repr__(self) -> str:
        return "UNSET"


UNSET = Unset()
