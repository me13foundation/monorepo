"""
Phenotype Hierarchy Domain Service.

Encapsulates business logic for HPO phenotype hierarchy navigation.
"""

from typing import List, Dict, Optional

from src.domain.entities.phenotype import Phenotype


class PhenotypeHierarchyService:
    """
    Domain service for phenotype hierarchy business logic.

    This service encapsulates the logic for navigating HPO hierarchies.
    """

    # Clinical categories and their associated HPO terms (simplified mapping)
    CLINICAL_CATEGORIES = {
        "congenital": ["HP:0000118"],  # Phenotypic abnormality
        "developmental": ["HP:0000118"],  # Phenotypic abnormality (broad)
        "neurological": ["HP:0000707"],  # Nervous system abnormality
        "cardiovascular": ["HP:0001626"],  # Cardiovascular system abnormality
        "musculoskeletal": ["HP:0003011"],  # Musculoskeletal system abnormality
        "endocrine": ["HP:0000818"],  # Endocrine system abnormality
        "oncological": ["HP:0002664"],  # Neoplasm
        "immunological": ["HP:0002715"],  # Immunodeficiency
        "other": ["HP:0000118"],  # Phenotypic abnormality (broad)
    }

    def __init__(self, phenotype_hierarchy: Optional[Dict[str, List[str]]] = None):
        """
        Initialize the hierarchy service.

        Args:
            phenotype_hierarchy: Optional pre-loaded hierarchy mapping
        """
        self._hierarchy = phenotype_hierarchy or {}
        self._reverse_hierarchy: Dict[str, List[str]] = {}
        self._category_cache: Dict[str, str] = {}

        self._build_reverse_hierarchy()

    def get_ancestors(
        self, phenotype: Phenotype, max_depth: Optional[int] = None
    ) -> List[Phenotype]:
        """
        Get all ancestors of a phenotype in the hierarchy.

        Args:
            phenotype: The phenotype to get ancestors for
            max_depth: Maximum depth to traverse (None for unlimited)

        Returns:
            List of ancestor phenotypes ordered from immediate parent to root
        """
        ancestors = []
        current_id = phenotype.identifier.hpo_id
        visited = set()
        depth = 0

        while current_id and current_id not in visited:
            visited.add(current_id)

            if max_depth is not None and depth >= max_depth:
                break

            parents = self._hierarchy.get(current_id, [])
            if not parents:
                break

            # For simplicity, take the first parent (HPO can have multiple inheritance)
            parent_id = parents[0]

            # Create parent phenotype using identifier
            from src.domain.value_objects.identifiers import PhenotypeIdentifier

            parent_identifier = PhenotypeIdentifier(
                hpo_id=parent_id, hpo_term=f"Parent of {phenotype.name}"
            )
            parent_phenotype = Phenotype(
                identifier=parent_identifier,
                name=f"Parent of {phenotype.name}",
                definition="",
                category=self.categorize_phenotype_by_hpo_id(parent_id),
            )

            ancestors.append(parent_phenotype)
            current_id = parent_id
            depth += 1

        return ancestors

    def categorize_phenotype_by_hpo_id(self, hpo_id: str) -> str:
        """
        Categorize a phenotype based on its HPO ID.

        Args:
            hpo_id: HPO identifier

        Returns:
            Appropriate clinical category
        """
        if hpo_id in self._category_cache:
            return self._category_cache[hpo_id]

        # Check against known category mappings
        for category, hpo_terms in self.CLINICAL_CATEGORIES.items():
            if any(hpo_id.startswith(term) for term in hpo_terms):
                self._category_cache[hpo_id] = category
                return category

        # Default categorization
        category = "other"  # Broad default
        self._category_cache[hpo_id] = category
        return category

    def assess_phenotype_severity(
        self, phenotypes: List[Phenotype]
    ) -> Dict[str, float]:
        """
        Assess the overall severity based on phenotype categories.

        Args:
            phenotypes: List of phenotypes to assess

        Returns:
            Dictionary with severity scores by category
        """
        category_counts: Dict[str, int] = {}

        # Count phenotypes by category
        for phenotype in phenotypes:
            category_counts[phenotype.category] = (
                category_counts.get(phenotype.category, 0) + 1
            )

        # Calculate severity scores (simplified logic)
        category_severity = {}
        for category, count in category_counts.items():
            # Base severity by category
            base_severity = self._get_category_base_severity(category)

            # Adjust by count (more phenotypes in a category = higher severity)
            adjusted_severity = min(1.0, base_severity * (1 + (count - 1) * 0.2))

            category_severity[category] = adjusted_severity

        return category_severity

    def _build_reverse_hierarchy(self) -> None:
        """Build the reverse hierarchy mapping (parent -> children)."""
        for child, parents in self._hierarchy.items():
            for parent in parents:
                if parent not in self._reverse_hierarchy:
                    self._reverse_hierarchy[parent] = []
                self._reverse_hierarchy[parent].append(child)

    def _get_category_base_severity(self, category: str) -> float:
        """Get the base severity score for a phenotype category."""
        severity_map = {
            "congenital": 0.3,
            "developmental": 0.7,
            "neurological": 0.9,
            "cardiovascular": 0.8,
            "musculoskeletal": 0.5,
            "endocrine": 0.6,
            "oncological": 0.9,
            "immunological": 0.7,
            "other": 0.5,
        }

        return severity_map.get(category, 0.5)
