"""
Flujo Architecture Compliance Tests for MED13 Resource Library.

These tests validate that the Flujo AI agent implementation adheres to:
- docs/flujo/agent_architecture.md
- docs/flujo/prod_guide.md
- docs/flujo/contract_oriented_ai.md
- docs/flujo/reasoning.md

The tests ensure:
1. Contract-first design with typed Pydantic models
2. Clean Architecture layer separation for agents
3. Evidence-first output patterns
4. Governance configuration compliance
5. Proper lifecycle management
6. Skill registry patterns
"""

import ast
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SRC_ROOT = PROJECT_ROOT / "src"


@pytest.mark.architecture
class TestFlujoContractCompliance:
    """Tests for contract-first design compliance."""

    def test_base_agent_contract_has_required_fields(self) -> None:
        """
        Verify BaseAgentContract has evidence-first fields.

        Per agent_architecture.md, every agent contract must include:
        - confidence_score: float (0.0-1.0)
        - rationale: str
        - evidence: list[EvidenceItem]
        """
        from src.domain.agents.contracts.base import BaseAgentContract

        # Check required fields exist
        fields = BaseAgentContract.model_fields

        assert "confidence_score" in fields, "Missing confidence_score field"
        assert "rationale" in fields, "Missing rationale field"
        assert "evidence" in fields, "Missing evidence field"

        # Verify confidence_score constraints
        confidence_field = fields["confidence_score"]
        assert confidence_field.annotation is float or "float" in str(
            confidence_field.annotation,
        ), "confidence_score should be float"

    def test_evidence_item_has_required_fields(self) -> None:
        """
        Verify EvidenceItem has required fields for auditability.

        Per agent_architecture.md, evidence items must include:
        - source_type: Literal (tool, db, paper, web, note, api)
        - locator: str (DOI, URL, query-id, etc.)
        - excerpt: str
        - relevance: float
        """
        from src.domain.agents.contracts.base import EvidenceItem

        fields = EvidenceItem.model_fields

        assert "source_type" in fields, "Missing source_type field"
        assert "locator" in fields, "Missing locator field"
        assert "excerpt" in fields, "Missing excerpt field"
        assert "relevance" in fields, "Missing relevance field"

    def test_query_generation_contract_extends_base(self) -> None:
        """
        Verify QueryGenerationContract extends BaseAgentContract.

        All domain-specific contracts should inherit from BaseAgentContract
        to ensure evidence-first output patterns.
        """
        from src.domain.agents.contracts.base import BaseAgentContract
        from src.domain.agents.contracts.query_generation import (
            QueryGenerationContract,
        )

        assert issubclass(
            QueryGenerationContract,
            BaseAgentContract,
        ), "QueryGenerationContract must extend BaseAgentContract"

    def test_query_generation_contract_has_domain_fields(self) -> None:
        """
        Verify QueryGenerationContract has query-specific fields.

        Per agent_architecture.md, query contracts should include:
        - decision: Literal["proceed", "escalate", "fallback"]
        - query: str
        - source_type: str
        """
        from src.domain.agents.contracts.query_generation import (
            QueryGenerationContract,
        )

        fields = QueryGenerationContract.model_fields

        assert "decision" in fields, "Missing decision field"
        assert "query" in fields, "Missing query field"
        assert "source_type" in fields, "Missing source_type field"


def _check_infrastructure_imports(directory: Path) -> list[str]:
    """Check directory for forbidden infrastructure imports."""
    violations: list[str] = []

    for py_file in directory.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue

        content = py_file.read_text()
        try:
            tree = ast.parse(content)
        except SyntaxError:
            continue

        file_violations = _extract_infrastructure_imports(py_file, tree)
        violations.extend(file_violations)

    return violations


def _extract_infrastructure_imports(py_file: Path, tree: ast.AST) -> list[str]:
    """Extract infrastructure import violations from AST."""
    violations: list[str] = []
    rel_path = py_file.relative_to(PROJECT_ROOT)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            violations.extend(
                f"{rel_path}: imports {alias.name}"
                for alias in node.names
                if "infrastructure" in alias.name
            )
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module
            and "infrastructure" in node.module
        ):
            violations.append(f"{rel_path}: imports from {node.module}")

    return violations


@pytest.mark.architecture
class TestFlujoCleanArchitecture:
    """Tests for Clean Architecture layer compliance in AI agents."""

    def test_domain_agents_no_infrastructure_imports(self) -> None:
        """
        Verify domain/agents/ does not import from infrastructure.

        Per Clean Architecture, domain layer must not depend on infrastructure.
        """
        domain_agents_dir = SRC_ROOT / "domain" / "agents"
        if not domain_agents_dir.exists():
            pytest.skip("domain/agents/ directory not found")

        violations = _check_infrastructure_imports(domain_agents_dir)

        assert (
            not violations
        ), "Domain layer imports from infrastructure:\n" + "\n".join(
            f"  - {v}" for v in violations
        )

    def test_infrastructure_llm_implements_domain_ports(self) -> None:
        """
        Verify infrastructure/llm/adapters implement domain ports.

        Per Clean Architecture, infrastructure should implement
        interfaces defined in the domain layer.
        """
        from src.domain.agents.ports.query_agent_port import QueryAgentPort
        from src.infrastructure.llm.adapters.query_agent_adapter import (
            FlujoQueryAgentAdapter,
        )

        # Check that adapter implements the port
        assert issubclass(
            FlujoQueryAgentAdapter,
            QueryAgentPort,
        ), "FlujoQueryAgentAdapter must implement QueryAgentPort"

    def test_agent_contexts_are_pydantic_models(self) -> None:
        """
        Verify agent contexts are typed Pydantic models.

        Per strict_dsl=true in flujo.toml, contexts must be typed.
        """
        from pydantic import BaseModel

        from src.domain.agents.contexts.base import BaseAgentContext
        from src.domain.agents.contexts.query_context import QueryGenerationContext

        assert issubclass(
            BaseAgentContext,
            BaseModel,
        ), "BaseAgentContext must be a Pydantic model"
        assert issubclass(
            QueryGenerationContext,
            BaseAgentContext,
        ), "QueryGenerationContext must extend BaseAgentContext"


@pytest.mark.architecture
class TestFlujoGovernanceCompliance:
    """Tests for governance configuration compliance."""

    def test_governance_config_has_required_fields(self) -> None:
        """
        Verify GovernanceConfig has required governance fields.

        Per prod_guide.md, governance config should include:
        - confidence_threshold: float
        - require_evidence: bool
        - hitl_threshold: float
        """
        from src.infrastructure.llm.config.governance import GovernanceConfig

        config = GovernanceConfig.from_environment()

        assert hasattr(config, "confidence_threshold")
        assert hasattr(config, "require_evidence")
        assert hasattr(config, "hitl_threshold")

        # Verify thresholds are valid
        assert 0.0 <= config.confidence_threshold <= 1.0
        assert 0.0 <= config.hitl_threshold <= 1.0

    def test_usage_limits_has_required_fields(self) -> None:
        """
        Verify UsageLimits has cost control fields.

        Per prod_guide.md, usage limits should include:
        - total_cost_usd
        - max_turns
        - max_tokens
        """
        from src.infrastructure.llm.config.governance import UsageLimits

        limits = UsageLimits.default()

        assert hasattr(limits, "total_cost_usd")
        assert hasattr(limits, "max_turns")
        assert hasattr(limits, "max_tokens")

    def test_governance_auto_approve_requires_evidence(self) -> None:
        """
        Verify auto-approval logic respects evidence requirement.

        Per contract_oriented_ai.md, decisions without evidence
        should not be auto-approved when require_evidence=True.
        """
        from src.infrastructure.llm.config.governance import GovernanceConfig

        config = GovernanceConfig(
            confidence_threshold=0.85,
            require_evidence=True,
        )

        # High confidence but no evidence - should not auto-approve
        assert not config.should_auto_approve(0.95, has_evidence=False)

        # High confidence with evidence - should auto-approve
        assert config.should_auto_approve(0.95, has_evidence=True)

        # Low confidence - should not auto-approve regardless
        assert not config.should_auto_approve(0.5, has_evidence=True)


@pytest.mark.architecture
class TestFlujoLifecycleCompliance:
    """Tests for lifecycle management compliance."""

    def test_lifecycle_manager_exists(self) -> None:
        """
        Verify FlujoLifecycleManager is available.

        Per prod_guide.md, proper lifecycle management is required
        for resource cleanup during shutdown.
        """
        from src.infrastructure.llm.state.lifecycle import FlujoLifecycleManager

        manager = FlujoLifecycleManager()

        # Should have register/unregister methods
        assert hasattr(manager, "register_runner")
        assert hasattr(manager, "unregister_runner")
        assert hasattr(manager, "shutdown")  # async shutdown method

    def test_adapter_has_close_method(self) -> None:
        """
        Verify adapters have proper cleanup methods.

        Per prod_guide.md, adapters should implement close()
        for resource cleanup.
        """
        from src.infrastructure.llm.adapters.query_agent_adapter import (
            FlujoQueryAgentAdapter,
        )

        # Check close method exists
        assert hasattr(FlujoQueryAgentAdapter, "close")

        # Verify it's async
        import inspect

        assert inspect.iscoroutinefunction(
            FlujoQueryAgentAdapter.close,
        ), "close() should be async"


@pytest.mark.architecture
class TestFlujoSkillRegistryCompliance:
    """Tests for skill registry compliance."""

    def test_skill_registry_exists(self) -> None:
        """
        Verify SkillRegistry is available for skill governance.

        Per agent_architecture.md, skills should be registered
        with proper metadata for governance.
        """
        from src.infrastructure.llm.skills.registry import SkillRegistry

        registry = SkillRegistry()

        assert hasattr(registry, "register")
        assert hasattr(registry, "get")  # get(skill_id) method
        assert hasattr(registry, "list_skills")

    def test_skills_have_required_metadata(self) -> None:
        """
        Verify registered skills have required metadata.

        Per agent_architecture.md, skills should have:
        - description
        - side_effects flag
        - input_schema
        """
        from src.infrastructure.llm.skills.registry import (
            get_skill_registry,
            register_all_skills,
        )

        # Register skills
        register_all_skills()
        registry = get_skill_registry()

        skills = registry.list_skills()
        if not skills:
            pytest.skip("No skills registered")

        for skill_id in skills:
            skill_def = registry.get(skill_id)  # Use get() method
            assert skill_def is not None, f"Skill {skill_id} not found"
            assert skill_def.description, f"Skill {skill_id} missing description"
            assert hasattr(
                skill_def,
                "side_effects",
            ), f"Skill {skill_id} missing side_effects"
            assert skill_def.input_schema, f"Skill {skill_id} missing input_schema"


@pytest.mark.architecture
class TestFlujoConfigCompliance:
    """Tests for flujo.toml configuration compliance."""

    def test_flujo_toml_exists(self) -> None:
        """Verify flujo.toml configuration file exists."""
        flujo_toml = PROJECT_ROOT / "flujo.toml"
        assert flujo_toml.exists(), "flujo.toml not found in project root"

    def test_flujo_toml_has_required_sections(self) -> None:
        """
        Verify flujo.toml has required sections.

        Per prod_guide.md, flujo.toml should include:
        - [settings]
        - [governance]
        - [cost]
        """
        import tomllib

        flujo_toml = PROJECT_ROOT / "flujo.toml"
        with open(flujo_toml, "rb") as f:
            config = tomllib.load(f)

        assert "settings" in config, "Missing [settings] section"
        assert "governance" in config, "Missing [governance] section"
        assert "cost" in config, "Missing [cost] section"

    def test_strict_dsl_enabled(self) -> None:
        """
        Verify strict_dsl is enabled in flujo.toml.

        Per prod_guide.md, strict_dsl should be true for type safety.
        """
        import tomllib

        flujo_toml = PROJECT_ROOT / "flujo.toml"
        with open(flujo_toml, "rb") as f:
            config = tomllib.load(f)

        settings = config.get("settings", {})
        strict_dsl = settings.get("strict_dsl", True)  # Default is True

        assert strict_dsl is True, "strict_dsl should be enabled for type safety"


@pytest.mark.architecture
def test_flujo_architecture_integration() -> None:
    """
    Integration test: Verify complete Flujo architecture is wired correctly.

    This test ensures all components can be imported and instantiated.
    """
    # Domain layer
    from src.domain.agents.contexts.query_context import QueryGenerationContext

    # Infrastructure layer
    from src.infrastructure.llm.config.governance import (
        GovernanceConfig,
        ShadowEvalConfig,
        UsageLimits,
    )
    from src.infrastructure.llm.skills.registry import SkillRegistry
    from src.infrastructure.llm.state.lifecycle import FlujoLifecycleManager

    # Verify instances can be created (use assertions to mark as used)
    governance = GovernanceConfig.from_environment()
    limits = UsageLimits.default()

    # Verify all infrastructure components can be instantiated
    assert ShadowEvalConfig() is not None
    assert SkillRegistry() is not None
    assert FlujoLifecycleManager() is not None

    # Verify context can be instantiated
    context = QueryGenerationContext(source_type="pubmed")

    assert context.source_type == "pubmed"
    assert governance.confidence_threshold > 0
    assert limits.total_cost_usd is not None
