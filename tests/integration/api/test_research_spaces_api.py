"""
Integration tests for Research Spaces API endpoints.

Tests API routes, authentication, authorization, and data persistence.
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.main import create_app
from src.models.database import Base
from src.models.database.research_space import (
    ResearchSpaceModel,
)
from src.models.database.user import UserModel


@pytest.fixture(scope="function")
def test_client(test_engine):
    """Create a test client for API testing."""
    # Reset schema for clean tests
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    app = create_app()
    client = TestClient(app)
    yield client

    # Cleanup
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def test_user(db_session):
    """Create a test user for authentication."""
    user = UserModel(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password="hashed_password",
        role="researcher",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_space(db_session, test_user):
    """Create a test research space."""
    space = ResearchSpaceModel(
        slug="test-space",
        name="Test Space",
        description="Test research space",
        owner_id=test_user.id,
        status="active",
    )
    db_session.add(space)
    db_session.commit()
    return space


class TestResearchSpacesAPI:
    """Test research spaces API endpoints."""

    def test_create_space_requires_authentication(self, test_client):
        """Test that creating a space requires authentication."""
        response = test_client.post(
            "/research-spaces",
            json={
                "name": "Test Space",
                "slug": "test-space",
                "description": "Test",
            },
        )
        assert response.status_code == 401

    def test_list_spaces_requires_authentication(self, test_client):
        """Test that listing spaces requires authentication."""
        response = test_client.get("/research-spaces")
        assert response.status_code == 401

    def test_get_space_requires_authentication(self, test_client, test_space):
        """Test that getting a space requires authentication."""
        response = test_client.get(f"/research-spaces/{test_space.id}")
        assert response.status_code == 401

    # Note: Full integration tests would require:
    # - JWT token generation and authentication
    # - Database fixtures with proper relationships
    # - Authorization testing (owner vs member vs non-member)
    # - CRUD operation testing
    # - Membership management testing
    # These are placeholders showing the test structure


class TestMembershipAPI:
    """Test membership management API endpoints."""

    def test_list_members_requires_authentication(self, test_client, test_space):
        """Test that listing members requires authentication."""
        response = test_client.get(f"/research-spaces/{test_space.id}/members")
        assert response.status_code == 401

    def test_invite_member_requires_authentication(self, test_client, test_space):
        """Test that inviting a member requires authentication."""
        response = test_client.post(
            f"/research-spaces/{test_space.id}/members",
            json={
                "user_id": str(uuid4()),
                "role": "viewer",
            },
        )
        assert response.status_code == 401

    # Note: Full integration tests would require:
    # - Authentication fixtures
    # - Authorization testing (admin vs non-admin)
    # - Membership workflow testing (invite, accept, decline)
    # - Role update testing
    # - Member removal testing
