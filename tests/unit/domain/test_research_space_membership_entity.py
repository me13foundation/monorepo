"""
Unit tests for ResearchSpaceMembership domain entity.

Tests membership entity behavior, validation, and business logic.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.domain.entities.research_space_membership import (
    MembershipRole,
    ResearchSpaceMembership,
)


class TestResearchSpaceMembershipEntity:
    def test_membership_creation_valid_data(self):
        """Test successful membership creation with valid data."""
        space_id = uuid4()
        user_id = uuid4()

        membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.RESEARCHER,
        )

        assert membership.space_id == space_id
        assert membership.user_id == user_id
        assert membership.role == MembershipRole.RESEARCHER
        assert membership.is_active is True
        assert membership.invited_by is None
        assert membership.invited_at is None
        assert membership.joined_at is None
        assert membership.id is not None
        assert isinstance(membership.created_at, datetime)
        assert isinstance(membership.updated_at, datetime)

    def test_membership_creation_with_invitation(self):
        """Test membership creation with invitation details."""
        space_id = uuid4()
        user_id = uuid4()
        inviter_id = uuid4()
        invited_at = datetime.now(UTC)

        membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.VIEWER,
            invited_by=inviter_id,
            invited_at=invited_at,
        )

        assert membership.invited_by == inviter_id
        assert membership.invited_at == invited_at
        assert membership.joined_at is None
        # Pending invitations are active by default, but not yet accepted
        assert membership.is_active is True
        assert membership.is_pending_invitation() is True

    def test_membership_is_owner(self):
        """Test is_owner business logic method."""
        space_id = uuid4()
        user_id = uuid4()

        owner_membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.OWNER,
        )
        assert owner_membership.is_owner() is True

        admin_membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.ADMIN,
        )
        assert admin_membership.is_owner() is False

    def test_membership_is_admin(self):
        """Test is_admin business logic method."""
        space_id = uuid4()
        user_id = uuid4()

        owner_membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.OWNER,
        )
        assert owner_membership.is_admin() is True

        admin_membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.ADMIN,
        )
        assert admin_membership.is_admin() is True

        curator_membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.CURATOR,
        )
        assert curator_membership.is_admin() is False

    def test_membership_has_permission(self):
        """Test has_permission business logic method."""
        space_id = uuid4()
        user_id = uuid4()

        admin_membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.ADMIN,
        )

        # Admin should have all permissions
        assert admin_membership.has_permission(MembershipRole.VIEWER) is True
        assert admin_membership.has_permission(MembershipRole.RESEARCHER) is True
        assert admin_membership.has_permission(MembershipRole.CURATOR) is True
        assert admin_membership.has_permission(MembershipRole.ADMIN) is True
        assert (
            admin_membership.has_permission(MembershipRole.OWNER) is False
        )  # Owner is higher

        viewer_membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.VIEWER,
        )

        # Viewer should only have viewer permission
        assert viewer_membership.has_permission(MembershipRole.VIEWER) is True
        assert viewer_membership.has_permission(MembershipRole.RESEARCHER) is False
        assert viewer_membership.has_permission(MembershipRole.ADMIN) is False

    def test_membership_can_invite_members(self):
        """Test can_invite_members business logic method."""
        space_id = uuid4()
        user_id = uuid4()

        owner_membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.OWNER,
        )
        assert owner_membership.can_invite_members() is True

        admin_membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.ADMIN,
        )
        assert admin_membership.can_invite_members() is True

        curator_membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.CURATOR,
        )
        assert curator_membership.can_invite_members() is False

    def test_membership_can_modify_members(self):
        """Test can_modify_members business logic method."""
        space_id = uuid4()
        user_id = uuid4()

        owner_membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.OWNER,
        )
        assert owner_membership.can_modify_members() is True

        admin_membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.ADMIN,
        )
        assert admin_membership.can_modify_members() is True

        curator_membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.CURATOR,
        )
        assert curator_membership.can_modify_members() is False

    def test_membership_can_remove_members(self):
        """Test can_remove_members business logic method."""
        space_id = uuid4()
        user_id = uuid4()

        owner_membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.OWNER,
        )
        assert owner_membership.can_remove_members() is True

        admin_membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.ADMIN,
        )
        assert admin_membership.can_remove_members() is True

        curator_membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.CURATOR,
        )
        assert curator_membership.can_remove_members() is False

    def test_membership_with_role(self):
        """Test with_role immutability pattern."""
        space_id = uuid4()
        user_id = uuid4()

        membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.VIEWER,
        )

        updated_membership = membership.with_role(MembershipRole.ADMIN)

        assert updated_membership.id == membership.id
        assert updated_membership.role == MembershipRole.ADMIN
        assert membership.role == MembershipRole.VIEWER  # Original unchanged
        assert updated_membership is not membership  # Different instance

    def test_membership_with_joined_at(self):
        """Test with_joined_at immutability pattern."""
        space_id = uuid4()
        user_id = uuid4()
        joined_at = datetime.now(UTC)

        membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.RESEARCHER,
        )

        updated_membership = membership.with_joined_at(joined_at)

        assert updated_membership.id == membership.id
        assert updated_membership.joined_at == joined_at
        assert membership.joined_at is None  # Original unchanged
        assert updated_membership is not membership  # Different instance

    def test_membership_with_status(self):
        """Test with_status immutability pattern."""
        space_id = uuid4()
        user_id = uuid4()

        membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.RESEARCHER,
            is_active=True,
        )

        deactivated_membership = membership.with_status(is_active=False)

        assert deactivated_membership.id == membership.id
        assert deactivated_membership.is_active is False
        assert membership.is_active is True  # Original unchanged
        assert deactivated_membership is not membership  # Different instance

    def test_membership_is_pending_invitation(self):
        """Test is_pending_invitation business logic method."""
        space_id = uuid4()
        user_id = uuid4()
        inviter_id = uuid4()
        invited_at = datetime.now(UTC)

        pending_membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.VIEWER,
            invited_by=inviter_id,
            invited_at=invited_at,
            joined_at=None,
        )
        assert pending_membership.is_pending_invitation() is True

        accepted_membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.VIEWER,
            invited_by=inviter_id,
            invited_at=invited_at,
            joined_at=datetime.now(UTC),
        )
        assert accepted_membership.is_pending_invitation() is False

        direct_membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.VIEWER,
        )
        assert direct_membership.is_pending_invitation() is False

    def test_membership_is_accepted(self):
        """Test is_accepted business logic method."""
        space_id = uuid4()
        user_id = uuid4()

        accepted_membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.VIEWER,
            joined_at=datetime.now(UTC),
        )
        assert accepted_membership.is_accepted() is True

        pending_membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.VIEWER,
            invited_at=datetime.now(UTC),
            joined_at=None,
        )
        assert pending_membership.is_accepted() is False

    def test_membership_immutability(self):
        """Test that membership entity is immutable."""
        space_id = uuid4()
        user_id = uuid4()

        membership = ResearchSpaceMembership(
            space_id=space_id,
            user_id=user_id,
            role=MembershipRole.VIEWER,
        )

        # Attempting to modify should raise exception
        with pytest.raises(Exception):  # Frozen model raises exception
            membership.role = MembershipRole.ADMIN  # type: ignore[assignment]
