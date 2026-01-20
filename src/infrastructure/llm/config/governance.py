"""
Governance configuration for AI agents.

Provides runtime governance settings including tool allowlists,
PII scrubbing, and usage limits.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GovernanceConfig:
    """
    Governance configuration for AI agent operations.

    Controls security and compliance settings for agent execution
    including tool gating, PII handling, and cost limits.
    """

    tool_allowlist: frozenset[str] = field(default_factory=frozenset)
    pii_scrub_enabled: bool = False
    pii_strong_mode: bool = False
    total_cost_usd_limit: float | None = None
    confidence_threshold: float = 0.85

    @classmethod
    def from_environment(cls) -> GovernanceConfig:
        """
        Create governance config from environment variables.

        Environment variables:
        - FLUJO_GOVERNANCE_TOOL_ALLOWLIST: Comma-separated tool IDs
        - FLUJO_GOVERNANCE_PII_SCRUB: Enable PII scrubbing (1/0)
        - FLUJO_GOVERNANCE_PII_STRONG: Enable strong PII mode (1/0)
        - FLUJO_GOVERNANCE_COST_LIMIT: Max cost in USD
        - FLUJO_GOVERNANCE_CONFIDENCE_THRESHOLD: Min confidence for auto-approval
        """
        allowlist_raw = os.getenv("FLUJO_GOVERNANCE_TOOL_ALLOWLIST", "")
        allowlist = frozenset(
            tool.strip() for tool in allowlist_raw.split(",") if tool.strip()
        )

        pii_scrub = os.getenv("FLUJO_GOVERNANCE_PII_SCRUB", "0") == "1"
        pii_strong = os.getenv("FLUJO_GOVERNANCE_PII_STRONG", "0") == "1"

        cost_limit_raw = os.getenv("FLUJO_GOVERNANCE_COST_LIMIT")
        cost_limit = float(cost_limit_raw) if cost_limit_raw else None

        threshold_raw = os.getenv("FLUJO_GOVERNANCE_CONFIDENCE_THRESHOLD", "0.85")
        threshold = float(threshold_raw)

        return cls(
            tool_allowlist=allowlist,
            pii_scrub_enabled=pii_scrub,
            pii_strong_mode=pii_strong,
            total_cost_usd_limit=cost_limit,
            confidence_threshold=threshold,
        )

    def is_tool_allowed(self, tool_id: str) -> bool:
        """
        Check if a tool is allowed by the governance policy.

        If no allowlist is configured, all tools are allowed.
        """
        if not self.tool_allowlist:
            return True
        return tool_id in self.tool_allowlist
