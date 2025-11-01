"""
Quality gate orchestrator for managing multiple validation pipelines.

Coordinates quality gates across different data sources, pipelines,
and validation scenarios, providing centralized quality control.
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from .quality_gate import QualityGate, GateResult
from .pipeline import ValidationPipeline, PipelineResult
from ..rules.base_rules import ValidationRuleEngine


@dataclass
class OrchestratorConfig:
    """Configuration for the quality gate orchestrator."""

    parallel_pipelines: int = 2
    enable_metrics: bool = True
    auto_quarantine: bool = True
    auto_reject: bool = False
    quality_thresholds: Dict[str, float] = None

    def __post_init__(self):
        if self.quality_thresholds is None:
            self.quality_thresholds = {
                "critical": 0.9,  # Must pass for release
                "high": 0.8,  # High quality standard
                "medium": 0.7,  # Acceptable quality
                "low": 0.5,  # Minimum acceptable
            }


@dataclass
class OrchestratorResult:
    """Result of orchestrator execution."""

    success: bool
    pipelines_executed: int
    pipelines_passed: int
    pipelines_failed: int
    total_entities_processed: int
    quarantined_entities: int
    rejected_entities: int
    gate_results: List[GateResult]
    pipeline_results: List[PipelineResult]
    execution_time: float
    quality_summary: Dict[str, Any]


class QualityGateOrchestrator:
    """
    Orchestrates multiple quality gates and validation pipelines.

    Provides centralized management of quality control across the entire
    MED13 data processing ecosystem, with support for multiple pipelines,
    data sources, and quality standards.
    """

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or OrchestratorConfig()
        self.pipelines: Dict[str, ValidationPipeline] = {}
        self.gates: Dict[str, QualityGate] = {}

        # Results storage
        self.execution_history: List[OrchestratorResult] = []
        self.metrics_store: Dict[str, Any] = {}

        # Callbacks
        self.on_pipeline_complete: Optional[
            Callable[[str, PipelineResult], None]
        ] = None
        self.on_quality_alert: Optional[Callable[[str, Dict[str, Any]], None]] = None

    def register_pipeline(self, name: str, pipeline: ValidationPipeline):
        """
        Register a validation pipeline.

        Args:
            name: Pipeline name
            pipeline: ValidationPipeline instance
        """
        self.pipelines[name] = pipeline

    def unregister_pipeline(self, name: str):
        """Unregister a pipeline."""
        self.pipelines.pop(name, None)

    def register_gate(self, gate: QualityGate):
        """Register a quality gate."""
        self.gates[gate.name] = gate

    def unregister_gate(self, name: str):
        """Unregister a quality gate."""
        self.gates.pop(name, None)

    def create_standard_pipeline(
        self, name: str, rule_engine: Optional[ValidationRuleEngine] = None
    ) -> ValidationPipeline:
        """
        Create a standard validation pipeline with common checkpoints.

        Args:
            name: Pipeline name
            rule_engine: Optional custom rule engine

        Returns:
            Configured ValidationPipeline
        """
        from .quality_gate import (
            create_parsing_gate,
            create_normalization_gate,
            create_relationship_gate,
        )

        pipeline = ValidationPipeline(rule_engine)

        # Add standard checkpoints
        pipeline.add_checkpoint(pipeline.checkpoints.keys(), [create_parsing_gate()])
        pipeline.add_checkpoint(
            pipeline.checkpoints.keys(), [create_normalization_gate()]
        )
        pipeline.add_checkpoint(
            pipeline.checkpoints.keys(), [create_relationship_gate()], required=False
        )

        self.register_pipeline(name, pipeline)
        return pipeline

    async def execute_pipeline(
        self,
        pipeline_name: str,
        data: Dict[str, List[Dict[str, Any]]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[PipelineResult]:
        """
        Execute a specific validation pipeline.

        Args:
            pipeline_name: Name of pipeline to execute
            data: Data to validate
            context: Optional execution context

        Returns:
            PipelineResult or None if pipeline not found
        """
        if pipeline_name not in self.pipelines:
            return None

        pipeline = self.pipelines[pipeline_name]

        # Execute pipeline
        result = await pipeline.run_full_pipeline(data)

        # Store results
        self._store_pipeline_result(pipeline_name, result)

        # Trigger callbacks
        if self.on_pipeline_complete:
            self.on_pipeline_complete(pipeline_name, result)

        # Check for quality alerts
        self._check_quality_alerts(pipeline_name, result)

        return result

    async def execute_all_pipelines(
        self,
        data_sources: Dict[str, Dict[str, List[Dict[str, Any]]]],
        parallel: bool = True,
    ) -> OrchestratorResult:
        """
        Execute all registered pipelines.

        Args:
            data_sources: Data sources mapped to pipelines (pipeline_name -> data)
            parallel: Whether to execute pipelines in parallel

        Returns:
            OrchestratorResult with comprehensive execution results
        """
        import time

        start_time = time.time()

        pipeline_results = []
        gate_results = []

        if parallel and len(data_sources) > 1:
            # Execute pipelines in parallel
            tasks = []
            for pipeline_name, data in data_sources.items():
                if pipeline_name in self.pipelines:
                    task = self.execute_pipeline(pipeline_name, data)
                    tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                pipeline_name = list(data_sources.keys())[i]
                if isinstance(result, Exception):
                    # Handle pipeline execution error
                    error_result = PipelineResult(
                        success=False,
                        checkpoints_passed=[],
                        checkpoints_failed=[],
                        gate_results=[],
                        processed_entities=0,
                        quarantined_entities=0,
                        rejected_entities=0,
                        execution_time=0.0,
                        summary={"error": str(result)},
                    )
                    pipeline_results.append(error_result)
                else:
                    pipeline_results.append(result)
                    if result:
                        gate_results.extend(result.gate_results)
        else:
            # Execute pipelines sequentially
            for pipeline_name, data in data_sources.items():
                result = await self.execute_pipeline(pipeline_name, data)
                if result:
                    pipeline_results.append(result)
                    gate_results.extend(result.gate_results)

        execution_time = time.time() - start_time

        # Calculate orchestrator-level statistics
        success = all(r.success for r in pipeline_results if r)
        pipelines_executed = len(pipeline_results)
        pipelines_passed = sum(1 for r in pipeline_results if r and r.success)
        pipelines_failed = pipelines_executed - pipelines_passed

        total_entities = sum(r.processed_entities for r in pipeline_results if r)
        quarantined_total = sum(r.quarantined_entities for r in pipeline_results if r)
        rejected_total = sum(r.rejected_entities for r in pipeline_results if r)

        quality_summary = self._calculate_quality_summary(
            pipeline_results, gate_results
        )

        result = OrchestratorResult(
            success=success,
            pipelines_executed=pipelines_executed,
            pipelines_passed=pipelines_passed,
            pipelines_failed=pipelines_failed,
            total_entities_processed=total_entities,
            quarantined_entities=quarantined_total,
            rejected_entities=rejected_total,
            gate_results=gate_results,
            pipeline_results=pipeline_results,
            execution_time=execution_time,
            quality_summary=quality_summary,
        )

        self.execution_history.append(result)
        return result

    def _store_pipeline_result(self, pipeline_name: str, result: PipelineResult):
        """Store pipeline execution results."""
        if not self.config.enable_metrics:
            return

        if pipeline_name not in self.metrics_store:
            self.metrics_store[pipeline_name] = []

        self.metrics_store[pipeline_name].append(
            {"timestamp": datetime.now(), "result": result}
        )

        # Keep only last 100 results per pipeline
        if len(self.metrics_store[pipeline_name]) > 100:
            self.metrics_store[pipeline_name] = self.metrics_store[pipeline_name][-100:]

    def _check_quality_alerts(self, pipeline_name: str, result: PipelineResult):
        """Check for quality alerts that require attention."""
        if not self.on_quality_alert or not result:
            return

        alerts = []

        # Check overall quality score
        if (
            result.summary.get("overall_quality_score", 1.0)
            < self.config.quality_thresholds["critical"]
        ):
            alerts.append(
                {
                    "type": "critical_quality_drop",
                    "pipeline": pipeline_name,
                    "message": (
                        f"Critical quality threshold not met: "
                        f"{result.summary['overall_quality_score']:.3f}"
                    ),
                    "severity": "critical",
                }
            )

        # Check failure rates
        total_issues = result.summary.get("total_issues", {})
        error_rate = total_issues.get("error", 0) / max(result.processed_entities, 1)

        if error_rate > 0.1:  # More than 10% errors
            alerts.append(
                {
                    "type": "high_error_rate",
                    "pipeline": pipeline_name,
                    "message": f"High error rate: {error_rate:.1%}",
                    "severity": "high",
                }
            )

        # Check quarantine/rejection rates
        quarantine_rate = result.quarantined_entities / max(
            result.processed_entities, 1
        )
        if quarantine_rate > 0.2:  # More than 20% quarantined
            alerts.append(
                {
                    "type": "high_quarantine_rate",
                    "pipeline": pipeline_name,
                    "message": f"High quarantine rate: {quarantine_rate:.1%}",
                    "severity": "medium",
                }
            )

        # Trigger alerts
        for alert in alerts:
            self.on_quality_alert(pipeline_name, alert)

    def _calculate_quality_summary(
        self, pipeline_results: List[PipelineResult], gate_results: List[GateResult]
    ) -> Dict[str, Any]:
        """Calculate quality summary across all pipelines."""
        if not pipeline_results:
            return {"overall_score": 0.0}

        # Aggregate quality scores
        total_score = 0.0
        total_weight = 0.0

        for result in pipeline_results:
            if result:
                weight = result.processed_entities or 1
                total_score += result.summary.get("overall_quality_score", 0.0) * weight
                total_weight += weight

        overall_score = total_score / total_weight if total_weight > 0 else 0.0

        # Quality distribution
        quality_distribution = {
            "excellent": 0,  # > 0.9
            "good": 0,  # 0.8-0.9
            "fair": 0,  # 0.7-0.8
            "poor": 0,  # < 0.7
        }

        for result in pipeline_results:
            if result:
                score = result.summary.get("overall_quality_score", 0.0)
                if score > 0.9:
                    quality_distribution["excellent"] += 1
                elif score > 0.8:
                    quality_distribution["good"] += 1
                elif score > 0.7:
                    quality_distribution["fair"] += 1
                else:
                    quality_distribution["poor"] += 1

        return {
            "overall_score": overall_score,
            "quality_distribution": quality_distribution,
            "total_issues": self._aggregate_issues(pipeline_results),
            "performance_metrics": self._calculate_performance_metrics(
                pipeline_results
            ),
        }

    def _aggregate_issues(
        self, pipeline_results: List[PipelineResult]
    ) -> Dict[str, int]:
        """Aggregate issues across all pipelines."""
        total_issues = {"error": 0, "warning": 0, "info": 0}

        for result in pipeline_results:
            if result:
                issues = result.summary.get("total_issues", {})
                for severity in total_issues:
                    total_issues[severity] += issues.get(severity, 0)

        return total_issues

    def _calculate_performance_metrics(
        self, pipeline_results: List[PipelineResult]
    ) -> Dict[str, Any]:
        """Calculate performance metrics across pipelines."""
        if not pipeline_results:
            return {}

        execution_times = [r.execution_time for r in pipeline_results if r]
        entities_processed = [r.processed_entities for r in pipeline_results if r]

        return {
            "avg_execution_time": (
                sum(execution_times) / len(execution_times) if execution_times else 0
            ),
            "total_entities_processed": sum(entities_processed),
            "avg_entities_per_second": sum(entities_processed)
            / max(sum(execution_times), 0.001),
            "pipeline_count": len(pipeline_results),
        }

    def get_pipeline_metrics(
        self, pipeline_name: Optional[str] = None, limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get metrics for pipelines.

        Args:
            pipeline_name: Optional specific pipeline name
            limit: Maximum number of recent results to return

        Returns:
            Dictionary with pipeline metrics
        """
        if pipeline_name:
            results = self.metrics_store.get(pipeline_name, [])[-limit:]
            return {
                pipeline_name: [
                    {
                        "timestamp": r["timestamp"],
                        "success": r["result"].success,
                        "quality_score": r["result"].summary.get(
                            "overall_quality_score", 0.0
                        ),
                        "issues": r["result"].summary.get("total_issues", {}),
                    }
                    for r in results
                ]
            }
        else:
            return {
                name: [
                    {
                        "timestamp": r["timestamp"],
                        "success": r["result"].success,
                        "quality_score": r["result"].summary.get(
                            "overall_quality_score", 0.0
                        ),
                    }
                    for r in results[-limit:]
                ]
                for name, results in self.metrics_store.items()
            }

    def get_quality_report(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """
        Generate a comprehensive quality report.

        Args:
            time_range_hours: Hours of history to include

        Returns:
            Quality report dictionary
        """
        cutoff_time = datetime.now() - timedelta(hours=time_range_hours)

        recent_results = [
            result
            for result in self.execution_history
            if result.execution_time
            and (datetime.now() - timedelta(seconds=result.execution_time))
            > cutoff_time
        ]

        if not recent_results:
            return {"message": "No recent quality data available"}

        # Aggregate recent quality metrics
        total_executions = len(recent_results)
        successful_executions = sum(1 for r in recent_results if r.success)
        success_rate = (
            successful_executions / total_executions if total_executions > 0 else 0
        )

        total_entities = sum(r.total_entities_processed for r in recent_results)
        total_quarantined = sum(r.quarantined_entities for r in recent_results)
        total_rejected = sum(r.rejected_entities for r in recent_results)

        quarantine_rate = total_quarantined / max(total_entities, 1)
        rejection_rate = total_rejected / max(total_entities, 1)

        return {
            "time_range_hours": time_range_hours,
            "total_executions": total_executions,
            "success_rate": success_rate,
            "total_entities_processed": total_entities,
            "quarantine_rate": quarantine_rate,
            "rejection_rate": rejection_rate,
            "quality_thresholds": self.config.quality_thresholds,
            "recommendations": self._generate_recommendations(
                success_rate, quarantine_rate, rejection_rate
            ),
        }

    def _generate_recommendations(
        self, success_rate: float, quarantine_rate: float, rejection_rate: float
    ) -> List[str]:
        """Generate quality improvement recommendations."""
        recommendations = []

        if success_rate < 0.9:
            recommendations.append("Consider reviewing and tightening quality gates")
        elif success_rate < 0.95:
            recommendations.append("Quality standards are good but could be improved")

        if quarantine_rate > 0.1:
            recommendations.append(
                "High quarantine rate suggests quality gate thresholds too strict"
            )
        elif quarantine_rate < 0.01:
            recommendations.append(
                "Very low quarantine rate may indicate quality gates are too lenient"
            )

        if rejection_rate > 0.05:
            recommendations.append(
                "High rejection rate indicates significant data quality issues"
            )

        if not recommendations:
            recommendations.append("Data quality standards are well-maintained")

        return recommendations

    def export_quality_report(self, filepath: Path, time_range_hours: int = 24):
        """
        Export quality report to file.

        Args:
            filepath: Path to export file
            time_range_hours: Hours of history to include
        """
        import json

        report = self.get_quality_report(time_range_hours)
        report["generated_at"] = datetime.now().isoformat()

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, default=str)
