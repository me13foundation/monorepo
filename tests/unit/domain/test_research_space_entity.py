"""
Unit tests for ResearchSpace domain entity.

Tests research space entity behavior, validation, and business logic.
"""

from datetime import datetime
from uuid import uuid4

import pytest

from src.domain.entities.research_space import ResearchSpace, SpaceStatus


class TestResearchSpaceEntity:
    def test_space_creation_valid_data(self):
        """Test successful research space creation with valid data."""
        owner_id = uuid4()
        space = ResearchSpace(
            slug="med13-research",
            name="MED13 Research",
            description="Research space for MED13 syndrome",
            owner_id=owner_id,
        )

        assert space.slug == "med13-research"
        assert space.name == "MED13 Research"
        assert space.description == "Research space for MED13 syndrome"
        assert space.owner_id == owner_id
        assert space.status == SpaceStatus.ACTIVE
        assert space.settings == {}
        assert space.tags == []
        assert space.id is not None
        assert isinstance(space.created_at, datetime)
        assert isinstance(space.updated_at, datetime)

    def test_space_creation_with_all_fields(self):
        """Test research space creation with all optional fields."""
        owner_id = uuid4()
        settings = {"theme": "dark", "notifications": True}
        tags = ["genetics", "rare-disease"]

        space = ResearchSpace(
            slug="med12-research",
            name="MED12 Research",
            description="Research space for MED12 syndrome",
            owner_id=owner_id,
            status=SpaceStatus.ACTIVE,
            settings=settings,
            tags=tags,
        )

        assert space.settings == settings
        assert space.tags == tags
        assert space.status == SpaceStatus.ACTIVE

    @pytest.mark.parametrize(
        "invalid_slug",
        [
            "MED13",  # uppercase
            "med13_research",  # underscore
            "med13.research",  # dot
            "med 13",  # space
            "med13@research",  # special char
            "ab",  # too short
            "a" * 51,  # too long
        ],
    )
    def test_space_creation_invalid_slug(self, invalid_slug):
        """Test research space creation fails with invalid slug."""
        owner_id = uuid4()
        # Pydantic validation errors can be ValueError or ValidationError
        # Check for slug validation error message
        with pytest.raises(
            (ValueError, Exception),
            match=r"(Slug must contain only|String should have)",
        ):
            ResearchSpace(
                slug=invalid_slug,
                name="Test Space",
                description="Test",
                owner_id=owner_id,
            )

    @pytest.mark.parametrize(
        "invalid_tag",
        [
            "MED13",  # uppercase
            "tag_with_underscore",  # underscore
            "tag.with.dot",  # dot
            "tag with space",  # space
            "tag@special",  # special char
        ],
    )
    def test_space_creation_invalid_tags(self, invalid_tag):
        """Test research space creation fails with invalid tags."""
        owner_id = uuid4()
        with pytest.raises(ValueError, match=r"Tag.*must contain only"):
            ResearchSpace(
                slug="test-space",
                name="Test Space",
                description="Test",
                owner_id=owner_id,
                tags=[invalid_tag],
            )

    def test_space_is_active(self):
        """Test is_active business logic method."""
        owner_id = uuid4()
        active_space = ResearchSpace(
            slug="active-space",
            name="Active Space",
            description="Test",
            owner_id=owner_id,
            status=SpaceStatus.ACTIVE,
        )
        assert active_space.is_active() is True

        inactive_space = ResearchSpace(
            slug="inactive-space",
            name="Inactive Space",
            description="Test",
            owner_id=owner_id,
            status=SpaceStatus.INACTIVE,
        )
        assert inactive_space.is_active() is False

    def test_space_can_be_modified_by_owner(self):
        """Test can_be_modified_by business logic method."""
        owner_id = uuid4()
        other_user_id = uuid4()

        space = ResearchSpace(
            slug="test-space",
            name="Test Space",
            description="Test",
            owner_id=owner_id,
        )

        assert space.can_be_modified_by(owner_id) is True
        assert space.can_be_modified_by(other_user_id) is False

    def test_space_with_updated_at(self):
        """Test with_updated_at immutability pattern."""
        owner_id = uuid4()
        space = ResearchSpace(
            slug="test-space",
            name="Test Space",
            description="Test",
            owner_id=owner_id,
        )

        original_updated_at = space.updated_at
        updated_space = space.with_updated_at()

        assert updated_space.id == space.id
        assert updated_space.updated_at > original_updated_at
        assert updated_space is not space  # Different instance

    def test_space_with_status(self):
        """Test with_status immutability pattern."""
        owner_id = uuid4()
        space = ResearchSpace(
            slug="test-space",
            name="Test Space",
            description="Test",
            owner_id=owner_id,
            status=SpaceStatus.ACTIVE,
        )

        archived_space = space.with_status(SpaceStatus.ARCHIVED)

        assert archived_space.id == space.id
        assert archived_space.status == SpaceStatus.ARCHIVED
        assert space.status == SpaceStatus.ACTIVE  # Original unchanged
        assert archived_space is not space  # Different instance

    def test_space_with_settings(self):
        """Test with_settings immutability pattern."""
        owner_id = uuid4()
        space = ResearchSpace(
            slug="test-space",
            name="Test Space",
            description="Test",
            owner_id=owner_id,
        )

        new_settings = {"key": "value"}
        updated_space = space.with_settings(new_settings)

        assert updated_space.id == space.id
        assert updated_space.settings == new_settings
        assert space.settings == {}  # Original unchanged
        assert updated_space is not space  # Different instance

    def test_space_with_tags(self):
        """Test with_tags immutability pattern."""
        owner_id = uuid4()
        space = ResearchSpace(
            slug="test-space",
            name="Test Space",
            description="Test",
            owner_id=owner_id,
        )

        new_tags = ["tag1", "tag2"]
        updated_space = space.with_tags(new_tags)

        assert updated_space.id == space.id
        assert updated_space.tags == new_tags
        assert space.tags == []  # Original unchanged
        assert updated_space is not space  # Different instance

    def test_space_immutability(self):
        """Test that space entity is immutable."""
        owner_id = uuid4()
        space = ResearchSpace(
            slug="test-space",
            name="Test Space",
            description="Test",
            owner_id=owner_id,
        )

        # Attempting to modify should raise AttributeError
        with pytest.raises(Exception):  # Frozen model raises exception
            space.name = "New Name"  # type: ignore[assignment]
