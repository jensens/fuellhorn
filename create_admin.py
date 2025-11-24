"""Script to create an initial admin user."""

from app.database import get_session
from app.models.user import Role
from app.services.auth_service import create_user


def main() -> None:
    """Create initial admin user."""
    with next(get_session()) as session:
        # Check if admin already exists
        from app.services.auth_service import get_user_by_username
        
        try:
            existing_admin = get_user_by_username(session, "admin")
            print(f"Admin user already exists: {existing_admin.username}")
            return
        except Exception:
            pass
        
        # Create admin user
        admin = create_user(
            session=session,
            username="admin",
            email="admin@fuellhorn.local",
            password="admin",
            role=Role.ADMIN,
        )
        
        print(f"Created admin user: {admin.username}")
        print(f"Email: {admin.email}")
        print("Password: admin")
        print("\nIMPORTANT: Change this password after first login!")


if __name__ == "__main__":
    main()
