"""Simplified validation pipeline used in the integration tests."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from statistics import mean
from typing import Any, Dict, List, Optional, Sequence

from ..rules.base_rules import ValidationResult, ValidationRuleEngine
from .quality_gate import GateResult, QualityGate


@dataclass
class CheckpointEntry:
    gates: List[QualityGate]
    required: bool


class _CheckpointRegistry(Dict[str, CheckpointEntry]):
    def keys(self) -> List[str]:  # type: ignore[override]
        return list(super().keys())


@dataclass
class StageEvaluation:
    stage: str
    results: List[ValidationResult]
    gate_results: List[GateResult]

    @property
    def passed(self) -> bool:
        return all(gate.passed for gate in self.gate_results)

    @property
    def quality_score(self) -> float:
        if not self.gate_results:
            return 1.0
        return mean(gate.quality_score for gate in self.gate_results)

    @property
    def actions(self) -> List[str]:
        actions: List[str] = []
        for gate in self.gate_results:
            actions.extend(gate.actions)
        return actions


class ValidationPipeline:
    def __init__(self, rule_engine: Optional[ValidationRuleEngine] = None) -> None:
        self.rule_engine = rule_engine or ValidationRuleEngine()
        self.checkpoints: _CheckpointRegistry = _CheckpointRegistry()

    def add_checkpoint(
        self,
        name: str,
        gates: Sequence[QualityGate],
        required: bool = True,
    ) -> None:
        self.checkpoints[name] = CheckpointEntry(gates=list(gates), required=required)

    async def validate_stage(
        self, stage_name: str, payload: Dict[str, Sequence[Dict[str, Any]]]
    ) -> Dict[str, object]:
        checkpoint = self.checkpoints.get(stage_name)
        if not checkpoint:
            return {"stage": stage_name, "passed": True, "actions": []}

        entity_results = self._collect_results(payload)
        gate_results: List[GateResult] = []
        for gate in checkpoint.gates:
            gate_results.append(gate.evaluate(entity_results))

        stage_evaluation = StageEvaluation(stage_name, entity_results, gate_results)
        # Simulate asynchronous workload to mirror original behaviour
        await asyncio.sleep(0)
        return {
            "stage": stage_name,
            "passed": stage_evaluation.passed,
            "quality_score": stage_evaluation.quality_score,
            "actions": stage_evaluation.actions,
            "entity_results": entity_results,
        }

    def _collect_results(
        self, payload: Dict[str, Sequence[Dict[str, Any]]]
    ) -> List[ValidationResult]:
        results: List[ValidationResult] = []
        for entity_collection, items in payload.items():
            entity_type = entity_collection.rstrip("s")
            for item in items:
                results.append(self.rule_engine.validate_entity(entity_type, item))
        return results


__all__ = ["ValidationPipeline"]
