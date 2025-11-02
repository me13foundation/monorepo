"""Simple orchestrator coordinating validation pipelines."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence

from .pipeline import ValidationPipeline
from ..reporting.metrics import MetricsCollector
from ..rules.base_rules import ValidationResult, ValidationSeverity


@dataclass
class PipelineExecutionResult:
    pipeline_name: str
    success: bool
    processed_entities: int
    execution_time: float
    stage_results: Dict[str, Dict[str, object]]


@dataclass
class BatchExecutionResult:
    success: bool
    results: Dict[str, PipelineExecutionResult]
    total_entities_processed: int
    execution_time: float


class QualityGateOrchestrator:
    def __init__(self) -> None:
        self._pipelines: Dict[str, ValidationPipeline] = {}
        self.on_quality_alert: Optional[Callable[[str, Dict[str, object]], None]] = None

    def register_pipeline(self, name: str, pipeline: ValidationPipeline) -> None:
        self._pipelines[name] = pipeline

    async def execute_pipeline(
        self, name: str, payload: Dict[str, Sequence[Dict[str, Any]]]
    ) -> Optional[PipelineExecutionResult]:
        pipeline = self._pipelines.get(name)
        if pipeline is None:
            return None

        start = time.perf_counter()
        stage_results: Dict[str, Dict[str, object]] = {}
        collected_results: List[ValidationResult] = []
        success = True

        for stage in pipeline.checkpoints.keys():
            result = await pipeline.validate_stage(stage, payload)
            entity_results = result.get("entity_results")
            if isinstance(entity_results, list):
                collected_results.extend(
                    result_item
                    for result_item in entity_results
                    if isinstance(result_item, ValidationResult)
                )
            stage_results[stage] = {
                key: value for key, value in result.items() if key != "entity_results"
            }
            if not result.get("passed", False):
                success = False
                if self.on_quality_alert:
                    self.on_quality_alert(name, {"stage": stage, "result": result})

        processed = 0
        for items in payload.values():
            processed += len(items)
        execution_time = time.perf_counter() - start

        collector = MetricsCollector.get_default_instance()
        if collector:
            quality_values: List[float] = []
            for result_data in stage_results.values():
                quality_value = result_data.get("quality_score")
                if isinstance(quality_value, (int, float)):
                    quality_values.append(float(quality_value))
            average_quality = (
                float(sum(quality_values) / len(quality_values))
                if quality_values
                else 1.0
            )
            error_count = 0
            warning_count = 0
            for validation_result in collected_results:
                issues = getattr(validation_result, "issues", [])
                for issue in issues:
                    severity = getattr(issue, "severity", None)
                    if severity is ValidationSeverity.ERROR:
                        error_count += 1
                    elif severity is ValidationSeverity.WARNING:
                        warning_count += 1

            collector.collect_pipeline_metrics(
                pipeline_name=name,
                execution_time=execution_time,
                entities_processed=processed,
                quality_score=average_quality,
                error_count=error_count,
                warning_count=warning_count,
            )

        return PipelineExecutionResult(
            pipeline_name=name,
            success=success,
            processed_entities=processed,
            execution_time=execution_time,
            stage_results=stage_results,
        )

    async def execute_all_pipelines(
        self, payloads: Dict[str, Dict[str, Sequence[Dict[str, Any]]]]
    ) -> BatchExecutionResult:
        start = time.perf_counter()
        tasks = [
            self.execute_pipeline(name, payloads[name])
            for name in payloads
            if name in self._pipelines
        ]

        results_list = await asyncio.gather(*tasks)
        results: Dict[str, PipelineExecutionResult] = {
            result.pipeline_name: result
            for result in results_list
            if result is not None
        }

        total_entities = sum(result.processed_entities for result in results.values())
        all_success = (
            all(result.success for result in results.values()) if results else True
        )

        return BatchExecutionResult(
            success=all_success,
            results=results,
            total_entities_processed=total_entities,
            execution_time=time.perf_counter() - start,
        )


__all__ = [
    "BatchExecutionResult",
    "PipelineExecutionResult",
    "QualityGateOrchestrator",
]
