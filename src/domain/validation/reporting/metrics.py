"""
Metrics collection and analysis for validation framework.

Provides comprehensive metrics collection, aggregation, and analysis
capabilities for monitoring validation performance and data quality.
"""

from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
from pathlib import Path

from ..rules.base_rules import ValidationResult


class MetricType(Enum):
    """Types of metrics collected."""

    COUNTER = "counter"  # Simple count
    GAUGE = "gauge"  # Point-in-time value
    HISTOGRAM = "histogram"  # Distribution of values
    TIMER = "timer"  # Duration measurements


@dataclass
class MetricValue:
    """A single metric measurement."""

    name: str
    value: Union[int, float]
    timestamp: datetime
    tags: Dict[str, str]
    metric_type: MetricType


@dataclass
class MetricSummary:
    """Summary statistics for a metric."""

    name: str
    count: int
    sum: float
    avg: float
    min: float
    max: float
    std_dev: float
    percentiles: Dict[str, float]
    time_range: str


class MetricsCollector:
    """
    Comprehensive metrics collection system for validation.

    Collects, aggregates, and analyzes validation performance metrics,
    data quality indicators, and system health measurements.
    """

    def __init__(self, retention_hours: int = 168):  # 1 week default
        self.metrics: List[MetricValue] = []
        self.retention_hours = retention_hours
        self.aggregates: Dict[str, Dict[str, Any]] = defaultdict(dict)

        # Callbacks for metric events
        self.on_metric_collected: Optional[Callable[[MetricValue], None]] = None
        self.on_threshold_exceeded: Optional[Callable[[str, float, float], None]] = None

        # Metric thresholds for alerts
        self.thresholds: Dict[str, float] = {
            "error_rate": 0.1,  # 10% error rate threshold
            "quality_score": 0.8,  # Minimum quality score
            "processing_time": 300,  # 5 minutes max processing time
        }

    def collect_validation_metrics(
        self,
        results: Union[ValidationResult, List[ValidationResult]],
        pipeline_name: str = "default",
        entity_type: str = "unknown",
    ):
        """
        Collect metrics from validation results.

        Args:
            results: Validation result(s) to analyze
            pipeline_name: Name of the validation pipeline
            entity_type: Type of entities validated
        """
        if isinstance(results, ValidationResult):
            results = [results]

        for result in results:
            tags = {
                "pipeline": pipeline_name,
                "entity_type": entity_type,
                "validation_level": "standard",
            }

            # Quality score
            self.record_metric(
                "validation.quality_score", result.score, MetricType.GAUGE, tags
            )

            # Issue counts by severity
            for issue in result.issues:
                severity = issue.get("severity", "info")
                self.increment_counter(f"validation.issues.{severity}", tags)

            # Overall validation status
            status = 1 if result.is_valid else 0
            self.record_metric("validation.status", status, MetricType.GAUGE, tags)

    def collect_pipeline_metrics(
        self,
        pipeline_name: str,
        execution_time: float,
        entities_processed: int,
        quality_score: float,
        error_count: int,
        warning_count: int,
    ):
        """
        Collect metrics from pipeline execution.

        Args:
            pipeline_name: Name of the pipeline
            execution_time: Total execution time in seconds
            entities_processed: Number of entities processed
            quality_score: Overall quality score
            error_count: Number of errors encountered
            warning_count: Number of warnings
        """
        tags = {"pipeline": pipeline_name}

        # Performance metrics
        self.record_metric(
            "pipeline.execution_time", execution_time, MetricType.TIMER, tags
        )
        self.record_metric(
            "pipeline.entities_processed", entities_processed, MetricType.COUNTER, tags
        )
        self.record_metric(
            "pipeline.throughput",
            entities_processed / max(execution_time, 0.001),
            MetricType.GAUGE,
            tags,
        )

        # Quality metrics
        self.record_metric(
            "pipeline.quality_score", quality_score, MetricType.GAUGE, tags
        )
        self.record_metric(
            "pipeline.error_count", error_count, MetricType.COUNTER, tags
        )
        self.record_metric(
            "pipeline.warning_count", warning_count, MetricType.COUNTER, tags
        )
        self.record_metric(
            "pipeline.error_rate",
            error_count / max(entities_processed, 1),
            MetricType.GAUGE,
            tags,
        )

    def collect_gate_metrics(
        self, gate_name: str, gate_result: Any, pipeline_name: str = "default"
    ):
        """
        Collect metrics from quality gate evaluation.

        Args:
            gate_name: Name of the quality gate
            gate_result: Result from gate evaluation
            pipeline_name: Pipeline name
        """
        tags = {"pipeline": pipeline_name, "gate": gate_name}

        # Gate evaluation metrics
        status_value = 1 if gate_result.status.value == "passed" else 0
        self.record_metric("gate.status", status_value, MetricType.GAUGE, tags)
        self.record_metric(
            "gate.quality_score", gate_result.quality_score, MetricType.GAUGE, tags
        )
        self.record_metric(
            "gate.evaluation_time", gate_result.evaluation_time, MetricType.TIMER, tags
        )

        # Issue counts
        for severity, count in gate_result.issue_counts.items():
            self.record_metric(
                f"gate.issues.{severity}", count, MetricType.COUNTER, tags
            )

    def record_metric(
        self,
        name: str,
        value: Union[int, float],
        metric_type: MetricType,
        tags: Optional[Dict[str, str]] = None,
    ):
        """
        Record a metric measurement.

        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            tags: Optional tags for categorization
        """
        metric = MetricValue(
            name=name,
            value=value,
            timestamp=datetime.now(),
            tags=tags or {},
            metric_type=metric_type,
        )

        self.metrics.append(metric)

        # Update aggregates
        self._update_aggregates(metric)

        # Check thresholds
        self._check_thresholds(metric)

        # Trigger callback
        if self.on_metric_collected:
            self.on_metric_collected(metric)

    def increment_counter(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        current_value = self.get_current_value(name, tags) or 0
        self.record_metric(name, current_value + 1, MetricType.COUNTER, tags)

    def get_current_value(
        self, name: str, tags: Optional[Dict[str, str]] = None
    ) -> Optional[float]:
        """Get the current value of a gauge metric."""
        matching_metrics = [
            m
            for m in reversed(self.metrics)
            if m.name == name and self._tags_match(m.tags, tags)
        ]

        return matching_metrics[0].value if matching_metrics else None

    def _tags_match(
        self, metric_tags: Dict[str, str], query_tags: Optional[Dict[str, str]]
    ) -> bool:
        """Check if metric tags match query tags."""
        if not query_tags:
            return True

        return all(metric_tags.get(k) == v for k, v in query_tags.items())

    def _update_aggregates(self, metric: MetricValue):
        """Update aggregate statistics for a metric."""
        key = f"{metric.name}:{','.join(sorted(metric.tags.items()))}"

        if key not in self.aggregates:
            self.aggregates[key] = {
                "name": metric.name,
                "tags": metric.tags.copy(),
                "count": 0,
                "sum": 0.0,
                "min": float("inf"),
                "max": float("-inf"),
                "values": [],
            }

        agg = self.aggregates[key]
        agg["count"] += 1
        agg["sum"] += metric.value
        agg["min"] = min(agg["min"], metric.value)
        agg["max"] = max(agg["max"], metric.value)
        agg["values"].append(metric.value)

        # Keep only recent values (last 1000)
        if len(agg["values"]) > 1000:
            agg["values"] = agg["values"][-1000:]

    def _check_thresholds(self, metric: MetricValue):
        """Check if metric exceeds defined thresholds."""
        if not self.on_threshold_exceeded:
            return

        threshold_key = metric.name.split(".")[-1]  # Use last part of metric name
        threshold = self.thresholds.get(threshold_key)

        if threshold is not None:
            if metric.name.endswith("error_rate") and metric.value > threshold:
                self.on_threshold_exceeded(metric.name, metric.value, threshold)
            elif metric.name.endswith("quality_score") and metric.value < threshold:
                self.on_threshold_exceeded(metric.name, metric.value, threshold)
            elif metric.name.endswith("execution_time") and metric.value > threshold:
                self.on_threshold_exceeded(metric.name, metric.value, threshold)

    def get_metric_summary(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None,
        time_range_hours: int = 24,
    ) -> Optional[MetricSummary]:
        """
        Get summary statistics for a metric.

        Args:
            name: Metric name
            tags: Optional tags to filter
            time_range_hours: Time range for analysis

        Returns:
            MetricSummary or None if no data
        """
        cutoff_time = datetime.now() - timedelta(hours=time_range_hours)

        # Find matching metrics
        matching_metrics = [
            m
            for m in self.metrics
            if m.name == name
            and self._tags_match(m.tags, tags)
            and m.timestamp >= cutoff_time
        ]

        if not matching_metrics:
            return None

        values = [m.value for m in matching_metrics]

        # Calculate statistics
        count = len(values)
        total = sum(values)
        avg = total / count
        min_val = min(values)
        max_val = max(values)

        # Standard deviation
        variance = sum((x - avg) ** 2 for x in values) / count
        std_dev = variance**0.5

        # Percentiles
        sorted_values = sorted(values)
        percentiles = {
            "50": sorted_values[int(count * 0.5)],
            "90": sorted_values[int(count * 0.9)],
            "95": sorted_values[int(count * 0.95)],
            "99": (
                sorted_values[int(count * 0.99)] if count >= 100 else sorted_values[-1]
            ),
        }

        return MetricSummary(
            name=name,
            count=count,
            sum=total,
            avg=avg,
            min=min_val,
            max=max_val,
            std_dev=std_dev,
            percentiles=percentiles,
            time_range=f"{time_range_hours}h",
        )

    def get_system_health_score(self) -> float:
        """
        Calculate overall system health score based on metrics.

        Returns:
            Health score from 0.0 (poor) to 1.0 (excellent)
        """
        health_factors = []

        # Quality score factor
        quality_summary = self.get_metric_summary("validation.quality_score")
        if quality_summary:
            health_factors.append(
                min(1.0, quality_summary.avg / 0.9)
            )  # Target 90% quality

        # Error rate factor
        error_rate_summary = self.get_metric_summary("validation.error_rate")
        if error_rate_summary:
            health_factors.append(
                max(0.0, 1.0 - error_rate_summary.avg * 10)
            )  # Penalize high error rates

        # Performance factor
        perf_summary = self.get_metric_summary("pipeline.execution_time")
        if perf_summary:
            # Penalize if average execution time > 5 minutes
            health_factors.append(max(0.0, 1.0 - (perf_summary.avg - 300) / 600))

        if not health_factors:
            return 0.5  # Neutral score if no data

        return sum(health_factors) / len(health_factors)

    def get_performance_report(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """
        Generate a performance report.

        Args:
            time_range_hours: Time range for analysis

        Returns:
            Performance report dictionary
        """
        report = {
            "time_range": f"{time_range_hours}h",
            "generated_at": datetime.now().isoformat(),
            "health_score": self.get_system_health_score(),
            "metrics": {},
        }

        # Key metrics to include
        key_metrics = [
            "validation.quality_score",
            "validation.error_rate",
            "pipeline.execution_time",
            "pipeline.throughput",
            "gate.status",
        ]

        for metric_name in key_metrics:
            summary = self.get_metric_summary(
                metric_name, time_range_hours=time_range_hours
            )
            if summary:
                report["metrics"][metric_name] = {
                    "count": summary.count,
                    "avg": round(summary.avg, 3),
                    "min": round(summary.min, 3),
                    "max": round(summary.max, 3),
                    "percentiles": {
                        k: round(v, 3) for k, v in summary.percentiles.items()
                    },
                }

        # Trend analysis
        report["trends"] = self._analyze_metric_trends(time_range_hours)

        return report

    def _analyze_metric_trends(self, time_range_hours: int) -> Dict[str, Any]:
        """Analyze metric trends over time."""
        trends = {}

        # Group metrics by hour
        hourly_data = defaultdict(lambda: defaultdict(list))

        cutoff_time = datetime.now() - timedelta(hours=time_range_hours)

        for metric in self.metrics:
            if metric.timestamp >= cutoff_time:
                hour_key = metric.timestamp.replace(minute=0, second=0, microsecond=0)
                hourly_data[hour_key][metric.name].append(metric.value)

        # Calculate trends for key metrics
        for hour, metrics in sorted(hourly_data.items()):
            for metric_name, values in metrics.items():
                if metric_name not in trends:
                    trends[metric_name] = []

                trends[metric_name].append(
                    {
                        "hour": hour.isoformat(),
                        "avg": sum(values) / len(values),
                        "count": len(values),
                    }
                )

        return trends

    def export_metrics(
        self, filepath: Path, format: str = "json", time_range_hours: int = 24
    ):
        """
        Export metrics to file.

        Args:
            filepath: Path to export file
            format: Export format ("json", "csv")
            time_range_hours: Time range for exported data
        """
        if format == "json":
            report = self.get_performance_report(time_range_hours)
            import json

            with open(filepath, "w") as f:
                json.dump(report, f, indent=2, default=str)
        elif format == "csv":
            self._export_csv_metrics(filepath, time_range_hours)

    def _export_csv_metrics(self, filepath: Path, time_range_hours: int):
        """Export metrics in CSV format."""
        cutoff_time = datetime.now() - timedelta(hours=time_range_hours)

        with open(filepath, "w") as f:
            f.write("timestamp,name,value,type,tags\n")

            for metric in self.metrics:
                if metric.timestamp >= cutoff_time:
                    tags_str = ";".join(f"{k}:{v}" for k, v in metric.tags.items())
                    f.write(
                        ",".join(
                            [
                                metric.timestamp.isoformat(),
                                metric.name,
                                str(metric.value),
                                metric.metric_type.value,
                                tags_str,
                            ]
                        )
                        + "\n"
                    )

    def cleanup_old_metrics(self):
        """Remove metrics older than retention period."""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)

        # Remove old metrics
        self.metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]

        # Clean up aggregates for metrics that no longer exist
        existing_keys = {
            f"{m.name}:{','.join(sorted(m.tags.items()))}" for m in self.metrics
        }
        self.aggregates = {
            k: v for k, v in self.aggregates.items() if k in existing_keys
        }

    def set_threshold(self, metric_key: str, threshold: float):
        """Set a threshold for metric alerting."""
        self.thresholds[metric_key] = threshold

    def get_alerts(self, time_range_hours: int = 1) -> List[Dict[str, Any]]:
        """
        Get recent metric alerts.

        Args:
            time_range_hours: Time range to check for alerts

        Returns:
            List of alert dictionaries
        """
        alerts = []
        cutoff_time = datetime.now() - timedelta(hours=time_range_hours)

        # Check recent metrics against thresholds
        for metric in self.metrics:
            if metric.timestamp >= cutoff_time:
                threshold_key = metric.name.split(".")[-1]
                threshold = self.thresholds.get(threshold_key)

                if threshold is not None:
                    is_alert = False
                    if metric.name.endswith("error_rate") and metric.value > threshold:
                        is_alert = True
                    elif (
                        metric.name.endswith("quality_score")
                        and metric.value < threshold
                    ):
                        is_alert = True
                    elif (
                        metric.name.endswith("execution_time")
                        and metric.value > threshold
                    ):
                        is_alert = True

                    if is_alert:
                        alerts.append(
                            {
                                "metric": metric.name,
                                "value": metric.value,
                                "threshold": threshold,
                                "timestamp": metric.timestamp.isoformat(),
                                "tags": metric.tags,
                            }
                        )

        return alerts
