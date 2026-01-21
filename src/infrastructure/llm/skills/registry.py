"""
Centralized skill registration for AI agents.

Provides a registry for all agent skills with governance
metadata and runtime gating support.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field

from src.infrastructure.llm.config.governance import GovernanceConfig
from src.type_definitions.common import JSONObject, JSONValue

logger = logging.getLogger(__name__)

# Type alias for skill callables - they take JSONObject and return JSONObject
SkillCallable = Callable[[JSONObject], JSONObject]
SkillFactory = Callable[..., SkillCallable]


@dataclass
class SkillDefinition:
    """
    Definition of a registered skill.

    Contains all metadata required for skill governance
    and execution.
    """

    id: str
    factory: SkillFactory
    description: str
    side_effects: bool = False
    input_schema: JSONObject = field(default_factory=dict)
    output_schema: JSONObject = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


class SkillRegistry:
    """
    Registry for AI agent skills.

    Provides centralized management of all skills with:
    - Namespace-based organization
    - Governance integration
    - Runtime gating
    """

    def __init__(self, governance: GovernanceConfig | None = None) -> None:
        """
        Initialize the skill registry.

        Args:
            governance: Optional governance configuration
        """
        self._skills: dict[str, SkillDefinition] = {}
        self._governance = governance or GovernanceConfig.from_environment()

    def register(  # noqa: PLR0913
        self,
        skill_id: str,
        factory: SkillFactory,
        description: str,
        *,
        side_effects: bool = False,
        input_schema: JSONObject | None = None,
        output_schema: JSONObject | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """
        Register a skill with the registry.

        Args:
            skill_id: Unique namespaced skill ID (e.g., "pubmed.search")
            factory: Callable that returns the skill implementation
            description: Human-readable description
            side_effects: Whether the skill has side effects
            input_schema: JSON schema for input validation
            output_schema: JSON schema for output validation
            tags: Optional tags for categorization
        """
        if skill_id in self._skills:
            logger.warning("Overwriting existing skill: %s", skill_id)

        self._skills[skill_id] = SkillDefinition(
            id=skill_id,
            factory=factory,
            description=description,
            side_effects=side_effects,
            input_schema=input_schema or {},
            output_schema=output_schema or {},
            tags=tags or [],
        )
        logger.debug("Registered skill: %s", skill_id)

    def get(self, skill_id: str) -> SkillDefinition | None:
        """
        Get a skill definition by ID.

        Args:
            skill_id: The skill ID to look up

        Returns:
            SkillDefinition if found, None otherwise
        """
        return self._skills.get(skill_id)

    def get_callable(self, skill_id: str, **kwargs: JSONValue) -> SkillCallable | None:
        """
        Get a skill's callable implementation.

        Args:
            skill_id: The skill ID to look up
            **kwargs: Arguments to pass to the factory

        Returns:
            The skill callable if found and allowed, None otherwise

        Raises:
            PermissionError: If skill is not in governance allowlist
        """
        skill = self._skills.get(skill_id)
        if skill is None:
            return None

        if not self._governance.is_tool_allowed(skill_id):
            msg = f"Skill '{skill_id}' is not in the governance allowlist"
            raise PermissionError(msg)

        return skill.factory(**kwargs)

    def list_skills(self) -> list[str]:
        """List all registered skill IDs."""
        return list(self._skills.keys())

    def list_allowed_skills(self) -> list[str]:
        """List skill IDs that pass governance checks."""
        return [
            skill_id
            for skill_id in self._skills
            if self._governance.is_tool_allowed(skill_id)
        ]

    def get_skills_by_tag(self, tag: str) -> list[SkillDefinition]:
        """Get all skills with a specific tag."""
        return [skill for skill in self._skills.values() if tag in skill.tags]


# Global registry instance
_global_registry: SkillRegistry | None = None


def get_skill_registry() -> SkillRegistry:
    """
    Get the global skill registry instance.

    Creates the registry on first access.
    """
    global _global_registry  # noqa: PLW0603
    if _global_registry is None:
        _global_registry = SkillRegistry()
    return _global_registry


def register_all_skills() -> None:
    """
    Register all application skills.

    Call this during application startup to ensure all
    skills are available for agents.
    """
    registry = get_skill_registry()

    # --- Query Validation Skills ---
    registry.register(
        skill_id="query.validate_pubmed",
        factory=lambda **_: validate_pubmed_query,
        description="Validate a PubMed Boolean query syntax. Read-only.",
        side_effects=False,
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "PubMed query to validate"},
            },
            "required": ["query"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "valid": {"type": "boolean"},
                "query": {"type": "string"},
                "issues": {"type": "array", "items": {"type": "string"}},
                "suggestions": {"type": "array", "items": {"type": "string"}},
            },
        },
        tags=["query", "pubmed", "validation"],
    )

    # --- Search Skills ---
    registry.register(
        skill_id="search.pubmed",
        factory=lambda **_: search_pubmed_stub,
        description="Execute a PubMed search query. Read-only API call.",
        side_effects=False,
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "PubMed search query"},
                "max_results": {
                    "type": "integer",
                    "description": "Maximum results to return",
                    "default": 10,
                },
            },
            "required": ["query"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer"},
                "results": {"type": "array"},
                "total_count": {"type": "integer"},
            },
        },
        tags=["search", "pubmed", "api"],
    )

    # --- Query Building Skills ---
    registry.register(
        skill_id="query.suggest_mesh_terms",
        factory=lambda **_: suggest_mesh_terms,
        description="Suggest MeSH terms for a given concept. Read-only.",
        side_effects=False,
        input_schema={
            "type": "object",
            "properties": {
                "concept": {
                    "type": "string",
                    "description": "Medical concept to look up",
                },
            },
            "required": ["concept"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "concept": {"type": "string"},
                "mesh_terms": {"type": "array", "items": {"type": "string"}},
                "found": {"type": "boolean"},
            },
        },
        tags=["query", "mesh", "vocabulary"],
    )

    # --- Evidence Skills ---
    registry.register(
        skill_id="evidence.extract_citations",
        factory=lambda **_: extract_citations_stub,
        description="Extract citations from text. Read-only.",
        side_effects=False,
        input_schema={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to extract citations from",
                },
            },
            "required": ["text"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "citations": {"type": "array"},
                "count": {"type": "integer"},
            },
        },
        tags=["evidence", "citations", "extraction"],
    )

    logger.info("Registered %d skills", len(registry.list_skills()))


# --- Skill Implementations ---


def validate_pubmed_query(payload: JSONObject) -> JSONObject:
    """
    Validate a PubMed Boolean query syntax.

    Checks for:
    - Balanced parentheses
    - Valid field tags
    - Proper Boolean operator usage
    """
    query = str(payload.get("query", ""))
    issues: list[str] = []
    suggestions: list[str] = []

    # Check balanced parentheses
    open_parens = query.count("(")
    close_parens = query.count(")")
    if open_parens != close_parens:
        issues.append(
            f"Unbalanced parentheses: {open_parens} open, {close_parens} close",
        )

    # Check for valid field tags
    valid_tags = {
        "[Title]",
        "[Abstract]",
        "[Title/Abstract]",
        "[MeSH Terms]",
        "[Author]",
        "[Journal]",
        "[Publication Type]",
        "[All Fields]",
    }
    # Simple pattern check for field tags
    import re

    found_tags = re.findall(r"\[[^\]]+\]", query)
    for tag in found_tags:
        if tag not in valid_tags:
            issues.append(f"Unknown field tag: {tag}")
            suggestions.append(
                f"Consider using one of: {', '.join(sorted(valid_tags))}",
            )

    # Check for proper Boolean operators (should be uppercase)
    lower_ops = ["and", "or", "not"]
    suggestions.extend(
        f"Use uppercase Boolean operator: {op.upper()}"
        for op in lower_ops
        if f" {op} " in query.lower() and f" {op.upper()} " not in query
    )

    # Check for empty query
    if not query.strip():
        issues.append("Query is empty")

    return {
        "valid": len(issues) == 0,
        "query": query,
        "issues": issues,
        "suggestions": suggestions,
    }


def search_pubmed_stub(payload: JSONObject) -> JSONObject:
    """
    Execute a PubMed search query.

    Note: This is a stub implementation. Connect to the actual
    PubMed E-utilities API or existing gateway for production use.
    """
    query = str(payload.get("query", ""))
    max_results_raw = payload.get("max_results", 10)
    max_results = (
        int(max_results_raw) if isinstance(max_results_raw, int | float) else 10
    )

    # Note: In production, connect to PubMedGateway from
    # src.infrastructure.discovery for actual search functionality
    results: list[JSONValue] = []

    return {
        "query": query,
        "max_results": max_results,
        "results": results,
        "total_count": 0,
        "status": "stub",
        "message": "Connect to PubMedGateway for actual search results",
    }


def suggest_mesh_terms(payload: JSONObject) -> JSONObject:
    """
    Suggest MeSH terms for a given medical concept.

    Note: This is a stub implementation. Connect to the NCBI
    MeSH database or existing vocabulary service for production use.
    """
    concept = str(payload.get("concept", "")).lower()

    # Common MeSH term mappings (stub data)
    mesh_mappings: dict[str, list[str]] = {
        "med13": ["MED13 protein, human", "Mediator Complex Subunit 13"],
        "heart": ["Heart", "Myocardium", "Cardiovascular System"],
        "cardiac": ["Heart", "Cardiac Output", "Cardiovascular Diseases"],
        "variant": ["Genetic Variation", "Sequence Analysis, DNA", "Mutation"],
        "mutation": ["Mutation", "Mutagenesis", "DNA Mutational Analysis"],
        "gene": ["Genes", "Gene Expression", "Genetic Phenomena"],
    }

    # Find matching terms
    mesh_terms: list[str] = []
    for key, terms in mesh_mappings.items():
        if key in concept:
            mesh_terms.extend(terms)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_terms: list[str] = []
    for term in mesh_terms:
        if term not in seen:
            seen.add(term)
            unique_terms.append(term)

    return {
        "concept": concept,
        "mesh_terms": unique_terms,
        "found": len(unique_terms) > 0,
        "status": "stub",
        "message": "Connect to MeSH vocabulary service for complete mappings",
    }


def extract_citations_stub(payload: JSONObject) -> JSONObject:
    """
    Extract citations from text.

    Note: This is a stub implementation. Use proper citation
    extraction libraries for production use.
    """
    text = str(payload.get("text", ""))

    # Simple DOI pattern matching (stub)
    import re

    doi_pattern = r"10\.\d{4,}/[^\s]+"
    dois = re.findall(doi_pattern, text)

    # Simple PMID pattern matching
    pmid_pattern = r"PMID:\s*(\d+)"
    pmids = re.findall(pmid_pattern, text)

    citations: list[JSONObject] = [{"type": "doi", "value": doi} for doi in dois]
    citations.extend({"type": "pmid", "value": pmid} for pmid in pmids)

    return {
        "citations": citations,
        "count": len(citations),
        "status": "stub",
        "message": "Basic pattern matching only. Use proper citation extraction for production.",
    }
