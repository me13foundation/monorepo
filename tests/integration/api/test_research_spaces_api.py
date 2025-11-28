"""
Integration tests for Research Spaces API endpoints.

Tests API routes, authentication, authorization, and data persistence.
"""

import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.domain.entities.user import UserRole
from src.infrastructure.security.jwt_provider import JWTProvider
from src.main import create_app
from src.models.database import Base
from src.models.database.research_space import (
    ResearchSpaceMembershipModel,
    ResearchSpaceModel,
)
from src.models.database.user import UserModel


def _auth_headers(user: UserModel) -> dict[str, str]:
    """Helper to build auth headers for tests.

    Includes both a real JWT (for parity with production) and test headers that
    allow the auth dependency to short-circuit in TESTING environments.
    """
    secret = os.getenv(
        "MED13_DEV_JWT_SECRET",
        "test-jwt-secret-0123456789abcdefghijklmnopqrstuvwxyz",
    )
    provider = JWTProvider(secret_key=secret)
    token = provider.create_access_token(user_id=user.id, role=user.role)
    return {
        "Authorization": f"Bearer {token}",
        "X-TEST-USER-ID": str(user.id),
        "X-TEST-USER-EMAIL": user.email,
        "X-TEST-USER-ROLE": user.role,
    }


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
        role=UserRole.RESEARCHER.value,
        status="active",
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

    def test_get_my_membership_404_when_not_member(
        self,
        test_client,
        db_session,
        test_user,
    ):
        """Current user should get 404 if not a member of the space."""
        other_owner = UserModel(
            email="owner@example.com",
            username="owner",
            full_name="Owner User",
            hashed_password="hashed_password",
            role=UserRole.RESEARCHER.value,
            status="active",
        )
        db_session.add(other_owner)
        db_session.flush()
        other_space = ResearchSpaceModel(
            slug="other-space",
            name="Other Space",
            description="Another test space",
            owner_id=other_owner.id,
            status="active",
        )
        db_session.add(other_space)
        db_session.commit()

        response = test_client.get(
            f"/research-spaces/{other_space.id}/membership/me",
            headers=_auth_headers(test_user),
        )
        assert response.status_code == 404

    def test_get_my_membership_returns_role_when_member(
        self,
        test_client,
        db_session,
        test_space,
        test_user,
    ):
        """Current user should receive their active membership with role."""
        # Seed an active membership for the user as admin
        membership_id = uuid4()
        db_session.execute(
            ResearchSpaceMembershipModel.__table__.insert(),
            {
                "id": membership_id,
                "space_id": test_space.id,
                "user_id": test_user.id,
                "role": "admin",
                "invited_by": test_user.id,
                "invited_at": datetime.now(UTC),
                "joined_at": datetime.now(UTC),
                "is_active": True,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            },
        )
        db_session.commit()

        response = test_client.get(
            f"/research-spaces/{test_space.id}/membership/me",
            headers=_auth_headers(test_user),
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["id"] == str(membership_id)
        assert payload["role"] == "admin"

    # Note: Full integration tests would require:
    # - Authentication fixtures
    # - Authorization testing (admin vs non-admin)
    # - Membership workflow testing (invite, accept, decline)
    # - Role update testing
    # - Member removal testing
