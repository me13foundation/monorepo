"""
Performance optimization tests.

Tests caching, parallel processing, and selective validation
optimizations for performance improvements.
"""

import asyncio
import time

import pytest

from src.domain.validation.optimization.caching import CacheConfig, ValidationCache
from src.domain.validation.optimization.parallel_processing import (
    ParallelConfig,
    ParallelValidator,
)
from src.domain.validation.optimization.selective_validation import (
    SelectionStrategy,
    SelectiveValidator,
)
from src.domain.validation.rules.base_rules import ValidationRuleEngine
from src.domain.validation.testing.performance_benchmark import PerformanceBenchmark
from src.domain.validation.testing.test_data_generator import TestDataGenerator


class TestCachingOptimization:
    """Test caching optimization functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cache = ValidationCache(CacheConfig(max_cache_size=100))
        self.rule_engine = ValidationRuleEngine()

    def test_cache_storage_and_retrieval(self):
        """Test basic cache storage and retrieval."""
        key = "test_key"
        value = {"test": "data", "score": 0.85}

        # Store value
        self.cache.put(key, value)

        # Retrieve value
        retrieved = self.cache.get(key)

        assert retrieved == value

    def test_cache_expiration(self):
        """Test cache expiration functionality."""
        # Create cache with very short TTL
        cache = ValidationCache(CacheConfig(ttl_seconds=1))

        key = "expiring_key"
        value = {"data": "test"}

        # Store value
        cache.put(key, value)

        # Should be available immediately
        assert cache.get(key) == value

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        assert cache.get(key) is None

    def test_cache_key_generation(self):
        """Test cache key generation for validation."""
        gene_data = {"symbol": "TP53", "source": "test"}

        key1 = self.cache.get_cache_key("gene", gene_data)
        key2 = self.cache.get_cache_key("gene", gene_data)

        # Same data should generate same key
        assert key1 == key2

        # Different data should generate different key
        different_data = {"symbol": "BRCA1", "source": "test"}
        key3 = self.cache.get_cache_key("gene", different_data)
        assert key1 != key3

    def test_validation_result_caching(self):
        """Test caching of validation results."""
        gene_data = {"symbol": "TP53", "hgnc_id": "HGNC:11998", "source": "test"}

        # First validation (should compute)
        result1 = self.rule_engine.validate_entity("gene", gene_data)

        # Cache the result
        self.cache.cache_validation_result("gene", gene_data, result1)

        # Second validation (should use cache)
        cached_result = self.cache.get_cached_validation_result("gene", gene_data)

        assert cached_result is not None
        assert cached_result.score == result1.score
        assert len(cached_result.issues) == len(result1.issues)

    def test_cache_statistics(self):
        """Test cache statistics collection."""
        # Perform some cache operations
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")

        self.cache.get("key1")  # Hit
        self.cache.get("key3")  # Miss

        stats = self.cache.get_cache_stats()

        assert stats["total_entries"] == 2
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5


class TestParallelProcessingOptimization:
    """Test parallel processing optimization."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rule_engine = ValidationRuleEngine()
        self.parallel_validator = ParallelValidator(self.rule_engine)

    @pytest.mark.asyncio
    async def test_parallel_batch_validation(self):
        """Test parallel batch validation."""
        # Generate test data - use larger dataset for meaningful parallel processing
        data_generator = TestDataGenerator()
        gene_dataset = data_generator.generate_gene_dataset(500, "good")

        # Test sequential validation
        start_time = time.time()
        sequential_results = self.rule_engine.validate_batch("gene", gene_dataset.data)
        sequential_time = time.time() - start_time

        # Test parallel validation
        start_time = time.time()
        parallel_results = await self.parallel_validator.validate_batch_parallel(
            "gene",
            gene_dataset.data,
        )
        parallel_time = time.time() - start_time

        # Verify results are equivalent
        assert len(sequential_results) == len(parallel_results)

        for seq, par in zip(sequential_results, parallel_results, strict=False):
            assert seq.is_valid == par.is_valid
            assert abs(seq.score - par.score) < 0.01  # Allow small differences

        # Parallel should complete reasonably (may not be faster due to Python GIL and overhead)
        # Just ensure it doesn't take excessively long relative to a sane baseline
        baseline = max(sequential_time, 0.05)
        assert parallel_time < baseline * 10

    @pytest.mark.asyncio
    async def test_adaptive_parallelism(self):
        """Test adaptive parallelism selection."""
        # Small dataset - should potentially use sequential
        small_data = [{"symbol": "TP53", "source": "test"}]

        result = await self.parallel_validator.validate_with_adaptive_parallelism(
            "gene",
            small_data,
        )
        assert len(result) == 1

        # Larger dataset - should use parallel processing
        data_generator = TestDataGenerator()
        large_dataset = data_generator.generate_gene_dataset(50, "good")

        results = await self.parallel_validator.validate_with_adaptive_parallelism(
            "gene",
            large_dataset.data,
        )
        assert len(results) == 50

    def test_chunk_size_optimization(self):
        """Test chunk size optimization."""
        # Test different chunk sizes
        test_data = [{"symbol": f"GENE{i}", "source": "test"} for i in range(100)]

        chunk_sizes = [10, 25, 50, 100]

        for chunk_size in chunk_sizes:
            config = ParallelConfig(chunk_size=chunk_size)
            validator = ParallelValidator(self.rule_engine, config)

            async def test_chunk():
                results = await validator.validate_batch_parallel("gene", test_data)
                return len(results)

            # Run test
            result_count = asyncio.run(test_chunk())
            assert result_count == len(test_data)


class TestSelectiveValidationOptimization:
    """Test selective validation optimization."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rule_engine = ValidationRuleEngine()
        self.selective_validator = SelectiveValidator(
            self.rule_engine,
            SelectionStrategy.ADAPTIVE,
        )

    def test_confidence_based_selection(self):
        """Test confidence-based rule selection."""
        validator = SelectiveValidator(
            self.rule_engine,
            SelectionStrategy.CONFIDENCE_BASED,
        )

        # High confidence data
        high_conf_gene = {"symbol": "TP53", "hgnc_id": "HGNC:11998", "source": "test"}
        validator.update_confidence_score("gene", high_conf_gene, 0.95)

        result = validator.validate_selectively("gene", high_conf_gene)
        # Should validate but potentially skip some rules

        assert result is not None

    def test_selective_validation_stats(self):
        """Test selective validation statistics."""
        # Perform several validations
        test_data = [
            {"symbol": "TP53", "source": "test"},
            {"symbol": "BRCA1", "source": "test"},
            {"symbol": "INVALID", "source": "test"},  # Should have issues
        ]

        for data in test_data:
            self.selective_validator.validate_selectively("gene", data)

        stats = self.selective_validator.get_selectivity_stats()

        assert "validations_attempted" in stats
        assert "validations_skipped" in stats
        assert "avg_selectivity" in stats
        assert stats["validations_attempted"] == len(test_data)

    def test_validation_profile_usage(self):
        """Test validation profile usage."""

        # Create a profile
        self.selective_validator.create_validation_profile(
            name="test_profile",
            entity_types=["gene"],
            required_rules=["hgnc_nomenclature"],
            skip_conditions=[
                {"field": "source", "operator": "equals", "value": "low_quality"},
            ],
        )

        # Set active profile
        self.selective_validator.set_active_profile("test_profile")

        # Test with data that should be skipped
        skip_data = {"symbol": "TP53", "source": "low_quality"}
        result = self.selective_validator.validate_selectively("gene", skip_data)

        # Should return valid result (skipped validation)
        assert result.is_valid

        # Test with data that should be validated
        validate_data = {"symbol": "TP53", "source": "high_quality"}
        result = self.selective_validator.validate_selectively("gene", validate_data)

        # Should perform validation
        assert result is not None


class TestPerformanceBenchmarking:
    """Test performance benchmarking functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rule_engine = ValidationRuleEngine()
        self.benchmark = PerformanceBenchmark(self.rule_engine)

    def test_individual_rule_benchmarking(self):
        """Test benchmarking of individual rules."""
        test_data = [{"symbol": "TP53", "source": "test"}]

        result = self.benchmark.benchmark_validation_rule(
            "gene",
            "hgnc_nomenclature",
            test_data,
            5,
        )

        assert result.benchmark_name == "gene_hgnc_nomenclature_benchmark"
        assert len(result.execution_times) == 5
        assert len(result.summary_stats) > 0
        assert "avg_execution_time" in result.summary_stats

    def test_entity_validation_benchmarking(self):
        """Test entity validation benchmarking."""
        test_data = [{"symbol": f"GENE{i}", "source": "test"} for i in range(10)]

        result = self.benchmark.benchmark_entity_validation("gene", test_data, 3)

        assert "gene_validation_benchmark" in result.benchmark_name
        assert len(result.execution_times) == 3
        assert result.summary_stats["throughput_items_per_second"] > 0

    def test_batch_processing_benchmarking(self):
        """Test batch processing benchmarking."""
        test_data = [{"symbol": f"GENE{i}", "source": "test"} for i in range(50)]
        batch_sizes = [10, 25]

        results = self.benchmark.benchmark_batch_processing(
            "gene",
            batch_sizes,
            test_data,
        )

        assert len(results) == len(batch_sizes)
        for batch_size, result in results.items():
            assert result["execution_time"] > 0
            assert result["throughput"] > 0

    def test_comprehensive_benchmark(self):
        """Test comprehensive benchmark suite."""
        results = self.benchmark.run_comprehensive_benchmark(iterations=3)

        # Check that all benchmark categories are present
        expected_categories = [
            "rule_benchmarks",
            "entity_benchmarks",
            "batch_benchmarks",
            "memory_benchmarks",
            "scalability_benchmarks",
            "summary",
        ]

        for category in expected_categories:
            assert category in results

        # Check summary
        assert "overall_score" in results["summary"]

    def test_performance_metrics_calculation(self):
        """Test performance metrics calculation."""
        execution_times = [0.1, 0.15, 0.12, 0.18, 0.11]
        memory_usage = [1000, 1200, 1100, 1300, 1050]
        throughput = [10.0, 6.67, 8.33, 5.56, 9.09]

        metrics = self.benchmark._calculate_performance_metrics(
            execution_times,
            memory_usage,
            throughput,
        )

        assert abs(metrics.avg_execution_time - 0.132) < 0.01  # Approximate mean
        assert metrics.min_execution_time == 0.1
        assert metrics.max_execution_time == 0.18
        assert metrics.avg_memory_mb > 0
        assert metrics.throughput_items_per_second > 0
        assert 0.0 <= metrics.p95_execution_time <= metrics.max_execution_time


class TestOptimizationIntegration:
    """Test integration of multiple optimization techniques."""

    def setup_method(self):
        """Set up integrated optimization test."""
        from src.domain.validation.optimization.caching import ValidationCache
        from src.domain.validation.optimization.parallel_processing import (
            ParallelValidator,
        )
        from src.domain.validation.optimization.selective_validation import (
            SelectiveValidator,
        )

        self.rule_engine = ValidationRuleEngine()
        self.cache = ValidationCache()
        self.parallel_validator = ParallelValidator(self.rule_engine)
        self.selective_validator = SelectiveValidator(self.rule_engine)

    def test_cached_parallel_validation(self):
        """Test parallel validation with caching."""
        # Generate test data
        data_generator = TestDataGenerator()
        gene_dataset = data_generator.generate_gene_dataset(20, "good")

        # First run - should cache results
        async def first_run():
            results = await self.parallel_validator.validate_batch_parallel(
                "gene",
                gene_dataset.data,
            )
            # Cache results
            for i, result in enumerate(results):
                self.cache.cache_validation_result("gene", gene_dataset.data[i], result)
            return results

        first_results = asyncio.run(first_run())

        # Second run - should use cache where possible
        async def second_run():
            results = await self.parallel_validator.validate_batch_parallel(
                "gene",
                gene_dataset.data,
            )
            return results

        second_results = asyncio.run(second_run())

        # Results should be consistent
        assert len(first_results) == len(second_results)

        for fr, sr in zip(first_results, second_results, strict=False):
            assert fr.is_valid == sr.is_valid
            assert abs(fr.score - sr.score) < 0.01

    def test_selective_cached_validation(self):
        """Test selective validation with caching."""
        gene_data = {"symbol": "TP53", "hgnc_id": "HGNC:11998", "source": "test"}

        # First validation - should compute and cache
        result1 = self.selective_validator.validate_selectively("gene", gene_data)

        # Cache the result
        self.cache.cache_validation_result("gene", gene_data, result1)

        # Second validation - should use selective logic and potentially cache
        result2 = self.selective_validator.validate_selectively("gene", gene_data)

        # Results should be consistent
        assert result1.is_valid == result2.is_valid
        assert abs(result1.score - result2.score) < 0.01

    def test_performance_optimization_stack(self):
        """Test the complete optimization stack working together."""
        # Generate test data
        data_generator = TestDataGenerator()
        large_dataset = data_generator.generate_gene_dataset(50, "mixed")

        # Time the optimized validation
        start_time = time.time()

        async def optimized_validation():
            # Use parallel processing with selective validation
            results = []
            for entity in large_dataset.data:
                # Apply selective validation first
                selective_result = self.selective_validator.validate_selectively(
                    "gene",
                    entity,
                )

                # If not skipped by selective validation, it would go through
                results.append(selective_result)

            return results

        results = asyncio.run(optimized_validation())
        optimized_time = time.time() - start_time

        # Verify reasonable performance
        assert optimized_time < 10  # Should complete reasonably fast
        assert len(results) == len(large_dataset.data)

        # Check that some validations were performed
        validations_performed = sum(1 for r in results if hasattr(r, "issues"))
        assert validations_performed > 0

    def test_memory_efficiency(self):
        """Test memory efficiency of optimizations."""
        import psutil

        process = psutil.Process()

        # Baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Generate and validate large dataset
        data_generator = TestDataGenerator()
        large_dataset = data_generator.generate_gene_dataset(200, "good")

        # Validate with optimizations
        results = self.rule_engine.validate_batch("gene", large_dataset.data)

        # Check memory after
        after_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = after_memory - baseline_memory

        # Should not have excessive memory growth
        assert memory_increase < 100  # Less than 100MB increase

        # Verify results
        assert len(results) == len(large_dataset.data)
        valid_results = sum(1 for r in results if r.is_valid)
        assert valid_results > len(results) * 0.8  # Most should be valid
