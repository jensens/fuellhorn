"""User (Benutzer) Model.

Repräsentiert einen Benutzer mit Authentifizierung und Rolle.
"""

import bcrypt
from datetime import datetime
from enum import Enum
from sqlalchemy import Column
from sqlalchemy.dialects.sqlite import JSON
from sqlmodel import Field
from sqlmodel import SQLModel
from typing import Any


class Role(str, Enum):
    """Verfügbare Benutzerrollen.

    Fuellhorn hat nur 2 Rollen (vereinfacht gegenüber VellenBase):
    - ADMIN: Voller Zugriff + Benutzerverwaltung + Konfiguration
    - USER: Artikel erfassen, entnehmen, durchsuchen
    """

    ADMIN = "admin"
    USER = "user"


class User(SQLModel, table=True):
    """Benutzer mit Authentifizierung und Rolle.

    Im Gegensatz zu VellenBase hat ein User nur EINE Rolle (nicht mehrere).
    """

    __tablename__ = "users"

    # Primary Key
    id: int | None = Field(default=None, primary_key=True)

    # Authentifizierung
    username: str = Field(index=True, unique=True)
    password_hash: str = Field(default="")
    email: str = Field(index=True, unique=True)

    # Rolle (nur eine Rolle, nicht mehrere wie bei VellenBase)
    role: str = Field(default=Role.USER.value)

    # Status
    is_active: bool = Field(default=True)

    # Login-Sicherheit (locked_until für manuelles Admin-Lock)
    locked_until: datetime | None = Field(default=None)

    # Remember-Me Token (für "Angemeldet bleiben" Feature)
    remember_token: str | None = Field(default=None)

    # User Preferences (JSON field for personal settings like smart defaults)
    # Structure: {
    #     "item_type_time_window": 30,  # Minutes
    #     "category_time_window": 30,   # Minutes
    #     "location_time_window": 60,   # Minutes
    #     "last_item_entry": {...}      # Last entered item data for smart defaults
    # }
    preferences: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: datetime | None = Field(default=None)

    def set_password(self, password: str) -> None:
        """Hasht das Passwort und speichert es.

        Args:
            password: Das Klartext-Passwort.
        """
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Prüft ob das Passwort korrekt ist.

        Args:
            password: Das zu prüfende Klartext-Passwort.

        Returns:
            True wenn das Passwort korrekt ist, sonst False.
        """
        return bool(
            bcrypt.checkpw(
                password.encode("utf-8"),
                self.password_hash.encode("utf-8"),
            )
        )

    def has_role(self, role: Role) -> bool:
        """Prüft ob der Benutzer eine bestimmte Rolle hat.

        Args:
            role: Die zu prüfende Rolle.

        Returns:
            True wenn der Benutzer die Rolle hat, sonst False.
        """
        return self.role == role.value

    def is_admin(self) -> bool:
        """Prüft ob der Benutzer ein Admin ist.

        Returns:
            True wenn der Benutzer Admin ist, sonst False.
        """
        return self.role == Role.ADMIN.value

    def __repr__(self) -> str:
        """String-Repräsentation."""
        role_names = {
            Role.ADMIN.value: "Admin",
            Role.USER.value: "User",
        }
        role_str = role_names.get(self.role, self.role)
        status = "aktiv" if self.is_active else "inaktiv"
        return f"<User {self.username} ({role_str}, {status})>"
