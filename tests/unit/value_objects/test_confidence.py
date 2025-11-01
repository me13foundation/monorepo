"""
Unit tests for confidence score value object.
"""

import pytest
from src.models.value_objects.confidence import ConfidenceScore, EvidenceLevel


class TestConfidenceScore:
    """Test ConfidenceScore value object."""

    def test_create_confidence_score(self):
        """Test creating a valid ConfidenceScore."""
        score = ConfidenceScore(
            score=0.85,
            level=EvidenceLevel.STRONG,
            sample_size=100,
            p_value=0.001,
            study_count=3,
            peer_reviewed=True,
            replicated=True,
        )

        assert score.score == 0.85
        assert score.level == EvidenceLevel.STRONG
        assert score.sample_size == 100
        assert score.p_value == 0.001
        assert score.study_count == 3
        assert score.peer_reviewed is True
        assert score.replicated is True

    def test_from_score_class_method(self):
        """Test creating ConfidenceScore from numeric score."""
        score = ConfidenceScore.from_score(0.9)

        assert score.score == 0.9
        assert score.level == EvidenceLevel.DEFINITIVE

    def test_from_score_automatic_level_assignment(self):
        """Test automatic level assignment based on score."""
        # Definitive
        score = ConfidenceScore.from_score(0.95)
        assert score.level == EvidenceLevel.DEFINITIVE

        # Strong
        score = ConfidenceScore.from_score(0.85)
        assert score.level == EvidenceLevel.STRONG

        # Moderate
        score = ConfidenceScore.from_score(0.65)
        assert score.level == EvidenceLevel.MODERATE

        # Supporting
        score = ConfidenceScore.from_score(0.45)
        assert score.level == EvidenceLevel.SUPPORTING

        # Weak
        score = ConfidenceScore.from_score(0.25)
        assert score.level == EvidenceLevel.WEAK

        # Disproven
        score = ConfidenceScore.from_score(0.1)
        assert score.level == EvidenceLevel.DISPROVEN

    def test_is_significant(self):
        """Test significance determination."""
        significant_score = ConfidenceScore(score=0.8, level=EvidenceLevel.STRONG)

        moderate_significant = ConfidenceScore(score=0.7, level=EvidenceLevel.MODERATE)

        weak_score = ConfidenceScore(score=0.3, level=EvidenceLevel.WEAK)

        disproven_score = ConfidenceScore(score=0.1, level=EvidenceLevel.DISPROVEN)

        assert significant_score.is_significant() is True
        assert moderate_significant.is_significant() is True
        assert weak_score.is_significant() is False
        assert disproven_score.is_significant() is False

    def test_requires_validation(self):
        """Test validation requirement determination."""
        needs_validation = ConfidenceScore(score=0.6, peer_reviewed=False)

        validated = ConfidenceScore(score=0.8, peer_reviewed=True)

        assert needs_validation.requires_validation() is True
        assert validated.requires_validation() is False

    def test_quality_description(self):
        """Test quality description generation."""
        strong_score = ConfidenceScore.from_score(0.9)
        moderate_score = ConfidenceScore.from_score(0.6)
        weak_score = ConfidenceScore.from_score(0.2)

        assert "Strong evidence" in strong_score.quality_description
        assert "Moderate evidence" in moderate_score.quality_description
        assert "Weak evidence" in weak_score.quality_description

    def test_string_representation(self):
        """Test string representation."""
        score = ConfidenceScore.from_score(0.85)

        assert str(score) == "strong (0.85)"

    def test_immutable(self):
        """Test that ConfidenceScore is immutable."""
        score = ConfidenceScore.from_score(0.8)

        with pytest.raises(
            Exception
        ):  # Pydantic raises ValidationError for frozen instances
            score.score = 0.9

    def test_invalid_score_range(self):
        """Test invalid score ranges."""
        with pytest.raises(ValueError):
            ConfidenceScore(score=1.5)  # Too high

        with pytest.raises(ValueError):
            ConfidenceScore(score=-0.5)  # Too low

    def test_invalid_p_value_range(self):
        """Test invalid p-value ranges."""
        with pytest.raises(ValueError):
            ConfidenceScore(score=0.8, p_value=1.5)  # Too high

        with pytest.raises(ValueError):
            ConfidenceScore(score=0.8, p_value=-0.1)  # Too low

    def test_level_consistency_validation(self):
        """Test that inconsistent level/score combinations are allowed but logged."""
        # This should work but might log a warning in real implementation
        score = ConfidenceScore(
            score=0.9,
            level=EvidenceLevel.WEAK,  # Inconsistent with score
        )

        assert score.score == 0.9
        assert score.level == EvidenceLevel.WEAK  # Allowed but inconsistent

    def test_default_values(self):
        """Test default values."""
        score = ConfidenceScore(score=0.7)

        assert score.level == EvidenceLevel.SUPPORTING
        assert score.sample_size is None
        assert score.p_value is None
        assert score.study_count is None
        assert score.peer_reviewed is False
        assert score.replicated is False
