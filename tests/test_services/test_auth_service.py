"""Tests for Auth Service - Remember Token functionality."""

from app.models.user import User
from app.services import auth_service
from collections.abc import Generator
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


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session) -> User:
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        is_active=True,
        role="user",
    )
    user.set_password("password123")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


class TestRememberToken:
    """Tests for Remember Token functionality."""

    def test_generate_remember_token(self, session: Session, test_user: User) -> None:
        """Test that generate_remember_token creates and stores a token."""
        # Initially no token
        assert test_user.remember_token is None

        # Generate token
        token = auth_service.generate_remember_token(session, test_user)

        # Token should be returned and stored
        assert token is not None
        assert len(token) > 20  # Should be a secure random string
        assert test_user.remember_token == token

    def test_revoke_remember_token(self, session: Session, test_user: User) -> None:
        """Test that revoke_remember_token clears the token."""
        # First generate a token
        token = auth_service.generate_remember_token(session, test_user)
        assert test_user.remember_token == token

        # Revoke the token
        auth_service.revoke_remember_token(session, test_user)

        # Token should be cleared
        assert test_user.remember_token is None

    def test_get_user_by_remember_token(self, session: Session, test_user: User) -> None:
        """Test that get_user_by_remember_token finds user with valid token."""
        # Generate token
        token = auth_service.generate_remember_token(session, test_user)

        # Should find user
        found_user = auth_service.get_user_by_remember_token(session, token)
        assert found_user is not None
        assert found_user.id == test_user.id

    def test_get_user_by_remember_token_not_found(self, session: Session) -> None:
        """Test that get_user_by_remember_token returns None for invalid token."""
        found_user = auth_service.get_user_by_remember_token(session, "invalid-token")
        assert found_user is None

    def test_revoked_token_not_found(self, session: Session, test_user: User) -> None:
        """Test that revoked token can no longer be used to find user."""
        # Generate and then revoke token
        token = auth_service.generate_remember_token(session, test_user)
        auth_service.revoke_remember_token(session, test_user)

        # Token should no longer work
        found_user = auth_service.get_user_by_remember_token(session, token)
        assert found_user is None
