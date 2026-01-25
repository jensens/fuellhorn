"""Script to create an initial admin user.

Supports environment variables for Kubernetes init container usage:
- ADMIN_USERNAME: Admin username (default: "admin")
- ADMIN_EMAIL: Admin email (default: "admin@fuellhorn.local")
- ADMIN_PASSWORD: Admin password (required, no default for security)
"""

from app.database import get_session
from app.models.user import Role
from app.services.auth_service import create_user
from app.services.auth_service import get_user_by_username
import os
from sqlmodel import Session


def create_admin_user(session: Session) -> bool:
    """Create initial admin user from environment variables.

    Args:
        session: Database session

    Returns:
        True if user was created, False if user already exists

    Raises:
        ValueError: If ADMIN_PASSWORD environment variable is not set
    """
    username = os.environ.get("ADMIN_USERNAME", "admin")
    email = os.environ.get("ADMIN_EMAIL", "admin@fuellhorn.local")
    password = os.environ.get("ADMIN_PASSWORD")

    if not password:
        raise ValueError("ADMIN_PASSWORD environment variable is required")

    # Check if admin already exists
    existing = get_user_by_username(session, username)
    if existing:
        print(f"Admin user already exists: {existing.username}")
        return False

    # Create admin user
    admin = create_user(
        session=session,
        username=username,
        email=email,
        password=password,
        role=Role.ADMIN,
    )

    print(f"Created admin user: {admin.username}")
    print(f"Email: {admin.email}")
    return True


def main() -> None:
    """CLI entry point for creating admin user."""
    with next(get_session()) as session:
        try:
            created = create_admin_user(session)
            if created:
                print("\nAdmin user created successfully.")
            else:
                print("\nNo changes made.")
        except ValueError as e:
            print(f"Error: {e}")
            raise SystemExit(1)


if __name__ == "__main__":
    main()
