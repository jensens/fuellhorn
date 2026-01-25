"""Script to create an initial admin user.

This script is for local development. In production/Kubernetes,
use the CLI command: fuellhorn create-admin

Supports environment variables:
- ADMIN_USERNAME: Admin username (default: "admin")
- ADMIN_EMAIL: Admin email (default: "admin@fuellhorn.local")
- ADMIN_PASSWORD: Admin password (required, no default for security)
"""

# Re-export from CLI module to avoid duplication
from app.cli import create_admin_user
from app.database import get_session


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
