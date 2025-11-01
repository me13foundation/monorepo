"""
Validation pipeline with integrated quality gates.

Provides a pipeline that automatically applies quality gates at
different stages of the ETL process, with configurable checkpoints.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from .quality_gate import QualityGate, GateResult, GateStatus, GateAction
from ..rules.base_rules import ValidationRuleEngine


class PipelineStage(Enum):
    """Stages in the validation pipeline."""

    PARSING = "parsing"
    NORMALIZATION = "normalization"
    MAPPING = "mapping"
    VALIDATION = "validation"
    EXPORT = "export"


@dataclass
class PipelineCheckpoint:
    """A checkpoint in the validation pipeline."""

    stage: PipelineStage
    gates: List[QualityGate]
    required: bool = True  # Whether pipeline should fail if checkpoint fails
    continue_on_failure: bool = False  # Whether to continue processing failed items


@dataclass
class PipelineResult:
    """Result of running a validation pipeline."""

    success: bool
    checkpoints_passed: List[str]
    checkpoints_failed: List[str]
    gate_results: List[GateResult]
    processed_entities: int
    quarantined_entities: int
    rejected_entities: int
    execution_time: float
    summary: Dict[str, Any]


class ValidationPipeline:
    """
    Validation pipeline with integrated quality gates.

    Orchestrates the application of quality gates throughout the ETL pipeline,
    providing automated quality control at each processing stage.
    """

    def __init__(self, rule_engine: Optional[ValidationRuleEngine] = None):
        self.rule_engine = rule_engine or ValidationRuleEngine()
        self.checkpoints: Dict[PipelineStage, PipelineCheckpoint] = {}
        self.quarantine_store: Dict[str, List[Dict[str, Any]]] = {}
        self.rejected_store: Dict[str, List[Dict[str, Any]]] = {}

        # Default pipeline configuration
        self._setup_default_pipeline()

        # Callbacks
        self.on_checkpoint_pass: Optional[
            Callable[[PipelineCheckpoint, GateResult], None]
        ] = None
        self.on_checkpoint_fail: Optional[
            Callable[[PipelineCheckpoint, GateResult], None]
        ] = None
        self.on_entity_quarantined: Optional[
            Callable[[Dict[str, Any], str], None]
        ] = None
        self.on_entity_rejected: Optional[Callable[[Dict[str, Any], str], None]] = None

    def _setup_default_pipeline(self):
        """Set up default quality checkpoints."""
        from .quality_gate import (
            create_parsing_gate,
            create_normalization_gate,
            create_relationship_gate,
        )

        # Parsing checkpoint
        self.add_checkpoint(PipelineStage.PARSING, [create_parsing_gate()])

        # Normalization checkpoint
        self.add_checkpoint(PipelineStage.NORMALIZATION, [create_normalization_gate()])

        # Relationship checkpoint
        self.add_checkpoint(
            PipelineStage.MAPPING, [create_relationship_gate()], required=False
        )

    def add_checkpoint(
        self,
        stage: PipelineStage,
        gates: List[QualityGate],
        required: bool = True,
        continue_on_failure: bool = False,
    ):
        """
        Add a quality checkpoint to the pipeline.

        Args:
            stage: Pipeline stage for the checkpoint
            gates: Quality gates to apply at this checkpoint
            required: Whether checkpoint failure should fail the entire pipeline
            continue_on_failure: Whether to continue processing failed entities
        """
        checkpoint = PipelineCheckpoint(
            stage=stage,
            gates=gates,
            required=required,
            continue_on_failure=continue_on_failure,
        )
        self.checkpoints[stage] = checkpoint

    def remove_checkpoint(self, stage: PipelineStage):
        """Remove a checkpoint from the pipeline."""
        self.checkpoints.pop(stage, None)

    async def validate_stage(
        self,
        stage: PipelineStage,
        entities: Dict[str, List[Dict[str, Any]]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validate entities at a specific pipeline stage.

        Args:
            stage: Pipeline stage to validate
            entities: Entities to validate (entity_type -> list of entities)
            context: Optional context information

        Returns:
            Dictionary with validation results and actions
        """
        if stage not in self.checkpoints:
            return {
                "passed": True,
                "message": f"No checkpoint configured for stage {stage.value}",
                "actions": {},
            }

        checkpoint = self.checkpoints[stage]
        gate_results = []
        actions = {"quarantine": [], "reject": [], "warn": [], "continue": []}

        # Apply each gate
        for gate in checkpoint.gates:
            if not gate.enabled:
                continue

            # Get entities for this gate's entity types
            gate_entities = []
            for entity_type in gate.entity_types:
                if entity_type in entities:
                    gate_entities.extend(entities[entity_type])

            if not gate_entities:
                continue

            # Validate entities
            validation_results = []
            for entity in gate_entities:
                result = self.rule_engine.validate_entity(
                    entity.get("entity_type", "unknown"), entity
                )
                validation_results.append(result)

            # Evaluate gate
            gate_result = gate.evaluate(validation_results, context)
            gate_results.append(gate_result)

            # Apply gate action
            if gate_result.status == GateStatus.FAILED:
                if gate_result.action == GateAction.QUARANTINE:
                    actions["quarantine"].extend(gate_entities)
                elif gate_result.action == GateAction.REJECT:
                    actions["reject"].extend(gate_entities)
                elif gate_result.action == GateAction.BLOCK:
                    # Blocking action handled at checkpoint level
                    pass
            elif gate_result.status == GateStatus.WARNING:
                actions["warn"].extend(gate_entities)
            else:
                actions["continue"].extend(gate_entities)

        # Determine overall checkpoint result
        has_failures = any(r.status == GateStatus.FAILED for r in gate_results)
        checkpoint_passed = not has_failures or checkpoint.continue_on_failure

        # Trigger callbacks
        for result in gate_results:
            if result.status == GateStatus.PASSED and self.on_checkpoint_pass:
                self.on_checkpoint_pass(checkpoint, result)
            elif (
                result.status in [GateStatus.FAILED, GateStatus.BLOCKED]
                and self.on_checkpoint_fail
            ):
                self.on_checkpoint_fail(checkpoint, result)

        return {
            "passed": checkpoint_passed,
            "required": checkpoint.required,
            "gate_results": gate_results,
            "actions": actions,
            "checkpoint": checkpoint.stage.value,
        }

    async def run_full_pipeline(
        self,
        raw_data: Dict[str, List[Dict[str, Any]]],
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> PipelineResult:
        """
        Run the complete validation pipeline.

        Args:
            raw_data: Raw data to validate through pipeline
            progress_callback: Optional callback for progress updates

        Returns:
            PipelineResult with complete pipeline execution results
        """
        import time

        start_time = time.time()

        # Simulate pipeline stages (in practice, this would integrate with actual ETL)
        stages = [
            PipelineStage.PARSING,
            PipelineStage.NORMALIZATION,
            PipelineStage.MAPPING,
            PipelineStage.VALIDATION,
        ]

        checkpoints_passed = []
        checkpoints_failed = []
        all_gate_results = []

        total_entities = sum(len(entities) for entities in raw_data.values())

        for i, stage in enumerate(stages):
            if progress_callback:
                progress = (i / len(stages)) * 100
                progress_callback(f"Validating {stage.value} stage", progress)

            # Simulate stage data (in practice, this would come from ETL pipeline)
            stage_data = self._simulate_stage_data(stage, raw_data)

            result = await self.validate_stage(stage, stage_data)

            all_gate_results.extend(result["gate_results"])

            if result["passed"]:
                checkpoints_passed.append(stage.value)
            else:
                checkpoints_failed.append(stage.value)
                if result["required"]:
                    # Required checkpoint failed, stop pipeline
                    break

            # Apply actions from this stage
            self._apply_actions(result["actions"])

        execution_time = time.time() - start_time

        # Calculate summary statistics
        summary = self._calculate_pipeline_summary(all_gate_results, total_entities)

        pipeline_result = PipelineResult(
            success=len(checkpoints_failed) == 0,
            checkpoints_passed=checkpoints_passed,
            checkpoints_failed=checkpoints_failed,
            gate_results=all_gate_results,
            processed_entities=total_entities,
            quarantined_entities=len(self.quarantine_store.get("total", [])),
            rejected_entities=len(self.rejected_store.get("total", [])),
            execution_time=execution_time,
            summary=summary,
        )

        return pipeline_result

    def _simulate_stage_data(
        self, stage: PipelineStage, raw_data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Simulate data at different pipeline stages."""
        # This is a simplified simulation - in practice, data would come from ETL pipeline
        if stage == PipelineStage.PARSING:
            # Raw parsed data
            return {
                k: [{"entity_type": k.rstrip("s"), **v} for v in vals]
                for k, vals in raw_data.items()
            }
        elif stage == PipelineStage.NORMALIZATION:
            # Normalized data
            return {
                k: [
                    {"entity_type": k.rstrip("s"), "normalized": True, **v}
                    for v in vals
                ]
                for k, vals in raw_data.items()
            }
        elif stage == PipelineStage.MAPPING:
            # Relationship data
            return {
                "relationships": [
                    {"entity_type": "relationship", "type": "gene_variant"}
                ]
            }
        else:
            # General validation
            return {
                k: [{"entity_type": k.rstrip("s"), **v} for v in vals]
                for k, vals in raw_data.items()
            }

    def _apply_actions(self, actions: Dict[str, List[Dict[str, Any]]]):
        """Apply gate actions to entities."""
        # Quarantine entities
        for entity in actions["quarantine"]:
            entity_type = entity.get("entity_type", "unknown")
            if entity_type not in self.quarantine_store:
                self.quarantine_store[entity_type] = []
            self.quarantine_store[entity_type].append(entity)

            if self.on_entity_quarantined:
                self.on_entity_quarantined(entity, "quality_gate_failure")

        # Reject entities
        for entity in actions["reject"]:
            entity_type = entity.get("entity_type", "unknown")
            if entity_type not in self.rejected_store:
                self.rejected_store[entity_type] = []
            self.rejected_store[entity_type].append(entity)

            if self.on_entity_rejected:
                self.on_entity_rejected(entity, "quality_gate_failure")

        # Update total counts
        self.quarantine_store["total"] = (
            self.quarantine_store.get("total", []) + actions["quarantine"]
        )
        self.rejected_store["total"] = (
            self.rejected_store.get("total", []) + actions["reject"]
        )

    def _calculate_pipeline_summary(
        self, gate_results: List[GateResult], total_entities: int
    ) -> Dict[str, Any]:
        """Calculate summary statistics for pipeline execution."""
        if not gate_results:
            return {"overall_quality_score": 0.0, "total_issues": 0}

        total_quality_score = sum(r.quality_score for r in gate_results) / len(
            gate_results
        )

        total_issues = {
            "error": sum(r.issue_counts.get("error", 0) for r in gate_results),
            "warning": sum(r.issue_counts.get("warning", 0) for r in gate_results),
            "info": sum(r.issue_counts.get("info", 0) for r in gate_results),
        }

        return {
            "overall_quality_score": total_quality_score,
            "total_issues": total_issues,
            "gates_evaluated": len(gate_results),
            "entities_processed": total_entities,
            "quarantined_count": len(self.quarantine_store.get("total", [])),
            "rejected_count": len(self.rejected_store.get("total", [])),
        }

    def get_quarantined_entities(
        self, entity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get quarantined entities.

        Args:
            entity_type: Optional entity type filter

        Returns:
            List of quarantined entities
        """
        if entity_type:
            return self.quarantine_store.get(entity_type, [])
        else:
            return self.quarantine_store.get("total", [])

    def get_rejected_entities(
        self, entity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get rejected entities.

        Args:
            entity_type: Optional entity type filter

        Returns:
            List of rejected entities
        """
        if entity_type:
            return self.rejected_store.get(entity_type, [])
        else:
            return self.rejected_store.get("total", [])

    def clear_quarantine(self):
        """Clear all quarantined entities."""
        self.quarantine_store.clear()

    def clear_rejections(self):
        """Clear all rejected entities."""
        self.rejected_store.clear()

    def get_pipeline_config(self) -> Dict[str, Any]:
        """Get current pipeline configuration."""
        return {
            "checkpoints": {
                stage.value: {
                    "gates": [gate.name for gate in checkpoint.gates],
                    "required": checkpoint.required,
                    "continue_on_failure": checkpoint.continue_on_failure,
                }
                for stage, checkpoint in self.checkpoints.items()
            },
            "quarantine_count": len(self.quarantine_store.get("total", [])),
            "rejected_count": len(self.rejected_store.get("total", [])),
        }
