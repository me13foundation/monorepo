"""
Performance benchmarking for validation framework.

Provides comprehensive performance testing and benchmarking capabilities
to measure validation rule execution speed, memory usage, and scalability.
"""

import time
import psutil
import statistics
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from ..rules.base_rules import ValidationRuleEngine


@dataclass
class BenchmarkResult:
    """Result of a performance benchmark."""

    benchmark_name: str
    execution_times: List[float]
    memory_usage: List[float]
    throughput_measurements: List[float]
    summary_stats: Dict[str, Any]
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class PerformanceMetrics:
    """Performance metrics for validation operations."""

    avg_execution_time: float
    median_execution_time: float
    min_execution_time: float
    max_execution_time: float
    std_dev_execution_time: float
    p95_execution_time: float
    p99_execution_time: float
    throughput_items_per_second: float
    memory_peak_mb: float
    memory_avg_mb: float
    cpu_percent_avg: float


class PerformanceBenchmark:
    """
    Performance benchmarking system for validation rules.

    Measures execution speed, memory usage, CPU utilization, and scalability
    of validation operations under various loads and configurations.
    """

    def __init__(
        self, rule_engine: Optional[ValidationRuleEngine] = None, iterations: int = 1000
    ):
        self.rule_engine = rule_engine or ValidationRuleEngine()
        self.default_iterations = iterations
        self.results: List[BenchmarkResult] = []

    def run_comprehensive_benchmark(
        self, iterations: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run a comprehensive performance benchmark suite.

        Args:
            iterations: Number of iterations for each benchmark

        Returns:
            Comprehensive benchmark results
        """
        iters = iterations or self.default_iterations

        results = {}

        # Individual rule benchmarks
        results["rule_benchmarks"] = self._benchmark_individual_rules(iters)

        # Entity validation benchmarks
        results["entity_benchmarks"] = self._benchmark_entity_validation(iters)

        # Batch processing benchmarks
        results["batch_benchmarks"] = self._benchmark_batch_processing(iters)

        # Memory usage benchmarks
        results["memory_benchmarks"] = self._benchmark_memory_usage(iters)

        # Scalability benchmarks
        results["scalability_benchmarks"] = self._benchmark_scalability()

        # Overall summary
        results["summary"] = self._create_benchmark_summary(results)

        return results

    def benchmark_validation_rule(
        self,
        entity_type: str,
        rule_name: str,
        test_data: List[Dict[str, Any]],
        iterations: int = 100,
    ) -> BenchmarkResult:
        """
        Benchmark a specific validation rule.

        Args:
            entity_type: Type of entity
            rule_name: Name of the rule to benchmark
            test_data: Test data to validate
            iterations: Number of iterations

        Returns:
            BenchmarkResult for the rule
        """
        execution_times = []
        memory_usage = []
        throughput_measurements = []

        process = psutil.Process()

        for i in range(iterations):
            # Memory before
            mem_before = process.memory_info().rss / 1024 / 1024  # MB

            start_time = time.perf_counter()

            # Execute validation with specific rule
            result = self.rule_engine.validate_entity(
                entity_type, test_data[i % len(test_data)], [rule_name]
            )

            end_time = time.perf_counter()

            # Memory after
            mem_after = process.memory_info().rss / 1024 / 1024  # MB

            execution_times.append(end_time - start_time)
            memory_usage.append(mem_after - mem_before)
            throughput_measurements.append(
                1.0 / (end_time - start_time)
            )  # items/second

        summary_stats = self._calculate_performance_metrics(
            execution_times, memory_usage, throughput_measurements
        )

        result = BenchmarkResult(
            benchmark_name=f"{entity_type}_{rule_name}_benchmark",
            execution_times=execution_times,
            memory_usage=memory_usage,
            throughput_measurements=throughput_measurements,
            summary_stats=summary_stats,
            timestamp=datetime.now(),
            metadata={
                "entity_type": entity_type,
                "rule_name": rule_name,
                "iterations": iterations,
                "test_data_size": len(test_data),
            },
        )

        self.results.append(result)
        return result

    def benchmark_entity_validation(
        self, entity_type: str, test_data: List[Dict[str, Any]], iterations: int = 100
    ) -> BenchmarkResult:
        """
        Benchmark complete entity validation.

        Args:
            entity_type: Type of entity to benchmark
            test_data: Test data to validate
            iterations: Number of iterations

        Returns:
            BenchmarkResult for entity validation
        """
        execution_times = []
        memory_usage = []
        throughput_measurements = []

        process = psutil.Process()

        for i in range(iterations):
            mem_before = process.memory_info().rss / 1024 / 1024

            start_time = time.perf_counter()

            # Full entity validation
            result = self.rule_engine.validate_entity(
                entity_type, test_data[i % len(test_data)]
            )

            end_time = time.perf_counter()

            mem_after = process.memory_info().rss / 1024 / 1024

            execution_times.append(end_time - start_time)
            memory_usage.append(mem_after - mem_before)
            throughput_measurements.append(1.0 / (end_time - start_time))

        summary_stats = self._calculate_performance_metrics(
            execution_times, memory_usage, throughput_measurements
        )

        result = BenchmarkResult(
            benchmark_name=f"{entity_type}_validation_benchmark",
            execution_times=execution_times,
            memory_usage=memory_usage,
            throughput_measurements=throughput_measurements,
            summary_stats=summary_stats,
            timestamp=datetime.now(),
            metadata={
                "entity_type": entity_type,
                "iterations": iterations,
                "test_data_size": len(test_data),
            },
        )

        self.results.append(result)
        return result

    def benchmark_batch_processing(
        self, entity_type: str, batch_sizes: List[int], test_data: List[Dict[str, Any]]
    ) -> Dict[str, BenchmarkResult]:
        """
        Benchmark batch processing performance.

        Args:
            entity_type: Type of entity
            batch_sizes: List of batch sizes to test
            test_data: Test data pool

        Returns:
            Dictionary mapping batch sizes to benchmark results
        """
        results = {}

        for batch_size in batch_sizes:
            execution_times = []
            memory_usage = []
            throughput_measurements = []

            process = psutil.Process()

            # Run multiple batches
            for i in range(
                max(10, 1000 // batch_size)
            ):  # Adjust iterations based on batch size
                batch_data = test_data[:batch_size]

                mem_before = process.memory_info().rss / 1024 / 1024

                start_time = time.perf_counter()

                # Batch validation
                self.rule_engine.validate_batch(entity_type, batch_data)

                end_time = time.perf_counter()

                mem_after = process.memory_info().rss / 1024 / 1024

                batch_time = end_time - start_time
                execution_times.append(batch_time)
                memory_usage.append(mem_after - mem_before)
                throughput_measurements.append(
                    len(batch_data) / batch_time
                )  # items/second

            summary_stats = self._calculate_performance_metrics(
                execution_times, memory_usage, throughput_measurements
            )

            result = BenchmarkResult(
                benchmark_name=f"{entity_type}_batch_{batch_size}_benchmark",
                execution_times=execution_times,
                memory_usage=memory_usage,
                throughput_measurements=throughput_measurements,
                summary_stats=summary_stats,
                timestamp=datetime.now(),
                metadata={
                    "entity_type": entity_type,
                    "batch_size": batch_size,
                    "iterations": len(execution_times),
                },
            )

            results[batch_size] = result
            self.results.append(result)

        return results

    def _benchmark_individual_rules(self, iterations: int) -> Dict[str, Any]:
        """Benchmark individual validation rules."""
        from ..rules.gene_rules import GeneValidationRules
        from ..rules.variant_rules import VariantValidationRules
        from ..rules.phenotype_rules import PhenotypeValidationRules

        results = {}

        # Gene rules
        gene_test_data = [{"symbol": f"GENE{i}", "source": "test"} for i in range(10)]
        for rule in GeneValidationRules.get_all_rules():
            result = self.benchmark_validation_rule(
                "gene", rule.rule, gene_test_data, iterations // 10
            )
            results[f"gene_{rule.rule}"] = result.summary_stats

        # Variant rules
        variant_test_data = [
            {"variant_id": f"VAR{i}", "source": "test"} for i in range(10)
        ]
        for rule in VariantValidationRules.get_all_rules():
            result = self.benchmark_validation_rule(
                "variant", rule.rule, variant_test_data, iterations // 10
            )
            results[f"variant_{rule.rule}"] = result.summary_stats

        # Phenotype rules
        phenotype_test_data = [
            {"hpo_id": f"HP:{1000 + i:07d}", "name": f"Phenotype {i}"}
            for i in range(10)
        ]
        for rule in PhenotypeValidationRules.get_all_rules():
            result = self.benchmark_validation_rule(
                "phenotype", rule.rule, phenotype_test_data, iterations // 10
            )
            results[f"phenotype_{rule.rule}"] = result.summary_stats

        return results

    def _benchmark_entity_validation(self, iterations: int) -> Dict[str, Any]:
        """Benchmark complete entity validation."""
        results = {}

        # Gene validation
        gene_data = [{"symbol": f"GENE{i}", "source": "test"} for i in range(100)]
        result = self.benchmark_entity_validation("gene", gene_data, iterations // 10)
        results["gene_validation"] = result.summary_stats

        # Variant validation
        variant_data = [{"variant_id": f"VAR{i}", "source": "test"} for i in range(100)]
        result = self.benchmark_entity_validation(
            "variant", variant_data, iterations // 10
        )
        results["variant_validation"] = result.summary_stats

        # Phenotype validation
        phenotype_data = [
            {"hpo_id": f"HP:{1000 + i:07d}", "name": f"Phenotype {i}"}
            for i in range(100)
        ]
        result = self.benchmark_entity_validation(
            "phenotype", phenotype_data, iterations // 10
        )
        results["phenotype_validation"] = result.summary_stats

        return results

    def _benchmark_batch_processing(self, iterations: int) -> Dict[str, Any]:
        """Benchmark batch processing performance."""
        results = {}

        test_data = [{"symbol": f"GENE{i}", "source": "test"} for i in range(1000)]
        batch_sizes = [10, 50, 100, 500]

        batch_results = self.benchmark_batch_processing("gene", batch_sizes, test_data)

        for batch_size, result in batch_results.items():
            results[f"batch_size_{batch_size}"] = result.summary_stats

        return results

    def _benchmark_memory_usage(self, iterations: int) -> Dict[str, Any]:
        """Benchmark memory usage patterns."""
        import gc

        results = {}

        # Test memory growth over time
        process = psutil.Process()
        memory_readings = []

        test_data = [{"symbol": f"GENE{i}", "source": "test"} for i in range(100)]

        for i in range(iterations):
            # Validate entity
            self.rule_engine.validate_entity("gene", test_data[i % len(test_data)])

            # Record memory
            memory_readings.append(process.memory_info().rss / 1024 / 1024)  # MB

            # Periodic garbage collection
            if i % 100 == 0:
                gc.collect()

        results["memory_usage_over_time"] = {
            "readings": memory_readings,
            "peak_memory": max(memory_readings),
            "avg_memory": statistics.mean(memory_readings),
            "memory_growth": memory_readings[-1] - memory_readings[0],
        }

        return results

    def _benchmark_scalability(self) -> Dict[str, Any]:
        """Benchmark scalability with increasing data sizes."""
        results = {}

        data_sizes = [100, 500, 1000, 5000]
        execution_times = []

        for size in data_sizes:
            test_data = [{"symbol": f"GENE{i}", "source": "test"} for i in range(size)]

            start_time = time.perf_counter()
            self.rule_engine.validate_batch("gene", test_data)
            end_time = time.perf_counter()

            execution_time = end_time - start_time
            execution_times.append(execution_time)

            results[f"data_size_{size}"] = {
                "execution_time": execution_time,
                "throughput": size / execution_time,
                "efficiency": execution_time / size,  # seconds per item
            }

        # Calculate scalability metrics
        results["scalability_analysis"] = {
            "execution_times": execution_times,
            "data_sizes": data_sizes,
            "scaling_factor": (
                execution_times[-1] / execution_times[0]
                if execution_times[0] > 0
                else 0
            ),
            "is_linear": self._check_linear_scaling(data_sizes, execution_times),
        }

        return results

    def _calculate_performance_metrics(
        self,
        execution_times: List[float],
        memory_usage: List[float],
        throughput: List[float],
    ) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics."""
        return PerformanceMetrics(
            avg_execution_time=statistics.mean(execution_times),
            median_execution_time=statistics.median(execution_times),
            min_execution_time=min(execution_times),
            max_execution_time=max(execution_times),
            std_dev_execution_time=(
                statistics.stdev(execution_times) if len(execution_times) > 1 else 0
            ),
            p95_execution_time=self._percentile(execution_times, 95),
            p99_execution_time=self._percentile(execution_times, 99),
            throughput_items_per_second=statistics.mean(throughput),
            memory_peak_mb=max(memory_usage) if memory_usage else 0,
            memory_avg_mb=statistics.mean(memory_usage) if memory_usage else 0,
            cpu_percent_avg=0.0,  # Would require CPU monitoring
        )

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile from data."""
        if not data:
            return 0.0

        data_sorted = sorted(data)
        index = (len(data) - 1) * (percentile / 100)
        lower = int(index)
        upper = lower + 1
        weight = index - lower

        if upper >= len(data):
            return data_sorted[lower]

        return data_sorted[lower] * (1 - weight) + data_sorted[upper] * weight

    def _check_linear_scaling(self, sizes: List[int], times: List[float]) -> bool:
        """Check if performance scales linearly with data size."""
        if len(sizes) < 2 or len(times) < 2:
            return False

        # Calculate scaling ratios
        size_ratios = [sizes[i] / sizes[0] for i in range(len(sizes))]
        time_ratios = [times[i] / times[0] for i in range(len(times))]

        # Check if time scaling is close to linear (within 20% tolerance)
        scaling_efficiency = [
            time_ratios[i] / size_ratios[i] for i in range(len(size_ratios))
        ]

        avg_efficiency = statistics.mean(scaling_efficiency)
        efficiency_variance = (
            statistics.variance(scaling_efficiency)
            if len(scaling_efficiency) > 1
            else 0
        )

        # Consider linear if efficiency variance is low (< 0.1) and average efficiency is reasonable
        return efficiency_variance < 0.1 and 0.8 <= avg_efficiency <= 1.2

    def _create_benchmark_summary(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create overall benchmark summary."""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_benchmarks": len(self.results),
            "performance_overview": {},
            "bottlenecks_identified": [],
            "recommendations": [],
        }

        # Performance overview
        if "entity_benchmarks" in all_results:
            entity_benchmarks = all_results["entity_benchmarks"]
            summary["performance_overview"] = {
                "avg_validation_time_ms": {
                    entity: bench.get("avg_execution_time", 0) * 1000
                    for entity, bench in entity_benchmarks.items()
                },
                "throughput_items_per_second": {
                    entity: bench.get("throughput_items_per_second", 0)
                    for entity, bench in entity_benchmarks.items()
                },
            }

        # Identify bottlenecks
        if "batch_benchmarks" in all_results:
            batch_results = all_results["batch_benchmarks"]
            # Find batch size with best performance
            best_batch = max(
                batch_results.keys(),
                key=lambda k: batch_results[k].get("throughput_items_per_second", 0),
            )
            summary["bottlenecks_identified"].append(
                f"Optimal batch size: {best_batch}"
            )

        # Generate recommendations
        summary["recommendations"] = self._generate_performance_recommendations(
            all_results
        )

        return summary

    def _generate_performance_recommendations(
        self, results: Dict[str, Any]
    ) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        # Check scalability
        if "scalability_benchmarks" in results:
            scalability = results["scalability_benchmarks"].get(
                "scalability_analysis", {}
            )
            if not scalability.get("is_linear", True):
                recommendations.append(
                    "Consider optimizing algorithms for better scalability"
                )

        # Check memory usage
        if "memory_benchmarks" in results:
            memory = results["memory_benchmarks"].get("memory_usage_over_time", {})
            if memory.get("memory_growth", 0) > 50:  # 50MB growth
                recommendations.append("Implement memory optimization strategies")

        # Check batch processing
        if "batch_benchmarks" in results:
            batch_results = results["batch_benchmarks"]
            throughputs = [
                r.get("throughput_items_per_second", 0) for r in batch_results.values()
            ]
            if throughputs and max(throughputs) > min(throughputs) * 2:
                recommendations.append("Optimize batch processing parameters")

        if not recommendations:
            recommendations.append("Performance is within acceptable ranges")

        return recommendations

    def export_benchmark_results(
        self, results: Dict[str, Any], filepath: Path, format: str = "json"
    ):
        """
        Export benchmark results to file.

        Args:
            results: Benchmark results to export
            filepath: Path to export file
            format: Export format
        """
        if format == "json":
            import json

            with open(filepath, "w") as f:
                json.dump(results, f, indent=2, default=str)
        elif format == "csv":
            self._export_csv_benchmarks(results, filepath)

    def _export_csv_benchmarks(self, results: Dict[str, Any], filepath: Path):
        """Export benchmark results in CSV format."""
        with open(filepath, "w") as f:
            f.write("benchmark_type,metric,value,unit\n")

            for benchmark_type, benchmark_data in results.items():
                if isinstance(benchmark_data, dict):
                    for metric, value in benchmark_data.items():
                        if isinstance(value, dict) and "avg_execution_time" in value:
                            # Performance metrics
                            f.write(
                                f"{benchmark_type},{metric},{value['avg_execution_time']:.6f},seconds\n"
                            )
                            f.write(
                                f"{benchmark_type},{metric},{value['throughput_items_per_second']:.2f},items_per_second\n"
                            )
                        elif isinstance(value, (int, float)):
                            f.write(f"{benchmark_type},{metric},{value},count\n")

    def get_performance_trends(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """
        Analyze performance trends over time.

        Args:
            time_range_hours: Time range for trend analysis

        Returns:
            Performance trend analysis
        """
        cutoff_time = datetime.now() - timedelta(hours=time_range_hours)

        recent_results = [r for r in self.results if r.timestamp >= cutoff_time]

        if not recent_results:
            return {"message": "No recent benchmark data available"}

        # Group by benchmark type
        trends = {}

        for result in recent_results:
            bench_type = result.benchmark_name.split("_")[0]  # Extract entity type

            if bench_type not in trends:
                trends[bench_type] = {
                    "execution_times": [],
                    "throughputs": [],
                    "timestamps": [],
                }

            trends[bench_type]["execution_times"].append(
                result.summary_stats.avg_execution_time
            )
            trends[bench_type]["throughputs"].append(
                result.summary_stats.throughput_items_per_second
            )
            trends[bench_type]["timestamps"].append(result.timestamp.isoformat())

        return trends
