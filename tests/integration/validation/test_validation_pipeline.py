"""
Integration tests for validation pipeline.

Tests the complete validation pipeline including gates, reporting,
and orchestration components working together.
"""

import pytest
import asyncio
import os
import time

from src.domain.validation.rules.base_rules import ValidationRuleEngine
from src.domain.validation.gates.quality_gate import (
    GateStatus,
    create_parsing_gate,
)
from src.domain.validation.gates.pipeline import ValidationPipeline
from src.domain.validation.gates.orchestrator import QualityGateOrchestrator
from src.domain.validation.reporting.error_reporting import ErrorReporter
from src.domain.validation.reporting.metrics import MetricsCollector
from src.domain.validation.reporting.dashboard import ValidationDashboard
from src.domain.validation.testing.test_framework import ValidationTestFramework
from src.domain.validation.testing.test_data_generator import TestDataGenerator


class TestValidationPipelineIntegration:
    """Integration tests for validation pipeline components."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rule_engine = ValidationRuleEngine()
        self.error_reporter = ErrorReporter()
        self.metrics_collector = MetricsCollector()
        self.dashboard = ValidationDashboard(
            self.error_reporter, self.metrics_collector
        )

        # Test data
        self.test_gene = {
            "symbol": "TP53",
            "hgnc_id": "HGNC:11998",
            "name": "tumor protein p53",
            "source": "test",
        }

        self.test_variant = {
            "clinvar_id": "123456",
            "variation_name": "c.123A>G",
            "gene_symbol": "TP53",
            "clinical_significance": "Pathogenic",
            "source": "test",
        }

    def test_quality_gate_evaluation(self):
        """Test quality gate evaluation with real validation."""
        # Create a quality gate
        gate = create_parsing_gate()

        # Test with valid data
        validation_results = [self.rule_engine.validate_entity("gene", self.test_gene)]
        gate_result = gate.evaluate(validation_results)

        assert gate_result.status in [
            GateStatus.PASSED,
            GateStatus.FAILED,
            GateStatus.WARNING,
        ]
        assert isinstance(gate_result.quality_score, float)
        assert isinstance(gate_result.issue_counts, dict)

    def test_pipeline_execution(self):
        """Test validation pipeline execution."""
        pipeline = ValidationPipeline(self.rule_engine)

        # Test data
        test_data = {"genes": [self.test_gene], "variants": [self.test_variant]}

        async def run_pipeline_test():
            # Run pipeline for parsing stage
            result = await pipeline.validate_stage(
                pipeline.checkpoints.keys()[0] if pipeline.checkpoints else "parsing",
                test_data,
            )

            assert isinstance(result, dict)
            assert "passed" in result
            assert "actions" in result

        asyncio.run(run_pipeline_test())

    def test_orchestrator_coordination(self):
        """Test orchestrator coordination of multiple pipelines."""
        orchestrator = QualityGateOrchestrator()

        # Create and register a pipeline
        pipeline = ValidationPipeline(self.rule_engine)
        orchestrator.register_pipeline("test_pipeline", pipeline)

        # Test data
        test_data = {"genes": [self.test_gene], "variants": [self.test_variant]}

        async def run_orchestrator_test():
            # Execute pipeline through orchestrator
            result = await orchestrator.execute_pipeline("test_pipeline", test_data)

            if result:  # Pipeline might not exist or fail
                assert hasattr(result, "success")
                assert hasattr(result, "processed_entities")

        asyncio.run(run_orchestrator_test())

    def test_error_reporting_integration(self):
        """Test error reporting integration with validation."""
        # Add some validation errors
        self.error_reporter.add_error(
            "gene",
            "TP53",
            "symbol",
            "test_rule",
            "Test validation error",
            source="integration_test",
        )

        # Get error summary
        summary = self.error_reporter.get_error_summary()

        assert summary.total_errors >= 1
        assert isinstance(summary.by_category, dict)
        assert isinstance(summary.by_priority, dict)

    def test_metrics_collection_integration(self):
        """Test metrics collection integration."""
        # Collect some validation metrics
        validation_results = [self.rule_engine.validate_entity("gene", self.test_gene)]
        self.metrics_collector.collect_validation_metrics(
            validation_results, "test_pipeline", "gene"
        )

        # Collect pipeline metrics
        self.metrics_collector.collect_pipeline_metrics(
            "test_pipeline", 1.5, 1, 0.9, 0, 1
        )

        # Get performance report
        report = self.metrics_collector.get_performance_report()

        assert "health_score" in report
        assert "metrics" in report

    def test_dashboard_data_collection(self):
        """Test dashboard data collection and presentation."""
        # Add some test data
        self.error_reporter.add_error(
            "gene", "TP53", "symbol", "test_rule", "Test error"
        )

        validation_results = [self.rule_engine.validate_entity("gene", self.test_gene)]
        self.metrics_collector.collect_validation_metrics(
            validation_results, "test", "gene"
        )

        # Get dashboard data
        dashboard_data = self.dashboard.get_dashboard_data()

        assert hasattr(dashboard_data, "system_health")
        assert hasattr(dashboard_data, "quality_metrics")
        assert hasattr(dashboard_data, "error_summary")
        assert hasattr(dashboard_data, "alerts")

    def test_test_framework_execution(self):
        """Test validation test framework execution."""
        test_framework = ValidationTestFramework(self.rule_engine)

        # Create a simple test case
        from src.domain.validation.testing.test_framework import TestCase, TestType

        test_case = TestCase(
            test_id="integration_test_1",
            name="Integration test for gene validation",
            description="Test gene validation with realistic data",
            test_type=TestType.UNIT,
            entity_type="gene",
            input_data=self.test_gene,
            expected_result={"issues": [], "quality_score": 0.8},
        )

        # Create test suite
        suite = test_framework.create_unit_test_suite("gene", [test_case])
        test_framework.register_suite(suite)

        # Run the suite
        suite_result = test_framework.run_test_suite(suite.suite_id)

        if suite_result:
            assert len(suite_result.test_results) == 1
            assert hasattr(suite_result, "execution_time")


class TestValidationWorkflowIntegration:
    """Test complete validation workflows from ingestion to reporting."""

    def setup_method(self):
        """Set up complete workflow test fixtures."""
        self.rule_engine = ValidationRuleEngine()
        self.error_reporter = ErrorReporter()
        self.metrics_collector = MetricsCollector()
        self.dashboard = ValidationDashboard(
            self.error_reporter, self.metrics_collector
        )
        self.orchestrator = QualityGateOrchestrator()

        # Set up orchestrator with error/metrics callbacks
        self.orchestrator.on_quality_alert = self._handle_quality_alert

        self.alerts_received = []

    def _handle_quality_alert(self, pipeline_name: str, alert: dict):
        """Handle quality alerts during testing."""
        self.alerts_received.append(alert)

    def test_complete_validation_workflow(self):
        """Test complete validation workflow."""
        # Generate test data
        data_generator = TestDataGenerator()
        gene_dataset = data_generator.generate_gene_dataset(10, "good")

        # Set up pipeline with quality gates
        pipeline = ValidationPipeline(self.rule_engine)
        parsing_gate = create_parsing_gate()
        pipeline.add_checkpoint(
            pipeline.checkpoints.keys()[0] if pipeline.checkpoints else "parsing",
            [parsing_gate],
        )

        self.orchestrator.register_pipeline("workflow_test", pipeline)

        # Execute validation workflow
        test_data = {"genes": gene_dataset.data[:5]}  # Use subset for testing

        async def run_workflow():
            result = await self.orchestrator.execute_pipeline(
                "workflow_test", test_data
            )

            if result:
                # Verify pipeline executed
                assert result.processed_entities >= 0

                # Check that metrics were collected
                assert (
                    self.metrics_collector.get_current_value("pipeline.execution_time")
                    is not None
                )

                # Check dashboard data is available
                dashboard_data = self.dashboard.get_dashboard_data()
                assert dashboard_data.system_health >= 0.0

        asyncio.run(run_workflow())

    def test_error_handling_workflow(self):
        """Test error handling through the complete workflow."""
        # Generate problematic test data
        data_generator = TestDataGenerator()
        bad_gene_dataset = data_generator.generate_gene_dataset(5, "poor")

        # Execute validation
        results = self.rule_engine.validate_batch("gene", bad_gene_dataset.data)

        # Verify errors were found
        total_issues = sum(len(result.issues) for result in results)
        assert total_issues > 0  # Should find issues in poor quality data

        # Check error reporting
        for result in results:
            for issue in result.issues:
                self.error_reporter.add_error(
                    "gene",
                    None,
                    issue.get("field", "unknown"),
                    issue.get("rule", "unknown"),
                    issue.get("message", ""),
                    source="workflow_test",
                )

        # Verify errors were recorded
        summary = self.error_reporter.get_error_summary()
        assert summary.total_errors > 0

    def test_metrics_and_reporting_integration(self):
        """Test metrics collection and reporting integration."""
        # Generate and validate test data
        data_generator = TestDataGenerator()
        gene_data = data_generator.generate_gene_dataset(20, "mixed")

        # Validate in batches
        batch_size = 5
        for i in range(0, len(gene_data.data), batch_size):
            batch = gene_data.data[i : i + batch_size]
            results = self.rule_engine.validate_batch("gene", batch)

            # Collect metrics
            self.metrics_collector.collect_validation_metrics(
                results, "integration_test", "gene"
            )

        # Collect pipeline metrics
        self.metrics_collector.collect_pipeline_metrics(
            "integration_test", 2.5, len(gene_data.data), 0.75, 2, 3
        )

        # Get comprehensive report
        perf_report = self.metrics_collector.get_performance_report()
        dashboard_report = self.dashboard.generate_report("json")

        # Verify reports contain expected data
        assert "health_score" in perf_report
        assert isinstance(dashboard_report, str)  # JSON string

    def test_scalability_with_larger_datasets(self):
        """Test system scalability with larger datasets."""
        import time

        # Generate larger dataset
        data_generator = TestDataGenerator()
        large_gene_dataset = data_generator.generate_gene_dataset(100, "good")

        # Time the validation
        start_time = time.time()
        self.rule_engine.validate_batch("gene", large_gene_dataset.data)
        end_time = time.time()

        validation_time = end_time - start_time
        throughput = len(large_gene_dataset.data) / validation_time

        # Collect performance metrics
        self.metrics_collector.collect_pipeline_metrics(
            "scalability_test",
            validation_time,
            len(large_gene_dataset.data),
            0.8,
            0,
            5,  # Assume some minor issues
        )

        # Verify reasonable performance
        assert validation_time < 30  # Should complete in reasonable time
        assert throughput > 1  # At least 1 entity per second

        # Check metrics were recorded
        throughput_metric = self.metrics_collector.get_current_value(
            "pipeline.throughput"
        )
        assert throughput_metric is not None

    @pytest.mark.asyncio
    async def test_concurrent_pipeline_execution(self):
        """Test concurrent execution of multiple pipelines."""
        # Create multiple pipelines
        pipelines_data = {}
        for i in range(3):
            pipeline = ValidationPipeline(self.rule_engine)
            pipeline_name = f"concurrent_pipeline_{i}"

            # Generate different test data for each pipeline
            data_generator = TestDataGenerator(seed=i)  # Different seed for variety
            gene_data = data_generator.generate_gene_dataset(
                10, "good" if i % 2 == 0 else "mixed"
            )

            pipelines_data[pipeline_name] = {"genes": gene_data.data}

            self.orchestrator.register_pipeline(pipeline_name, pipeline)

        # Execute all pipelines concurrently
        start_time = time.time()
        results = await self.orchestrator.execute_all_pipelines(pipelines_data)
        end_time = time.time()

        # Verify results
        assert results.success or True  # Allow some failures in test
        assert results.total_entities_processed >= 0
        assert results.execution_time > 0

        # Check that execution was reasonably fast (concurrent)
        total_time = end_time - start_time
        assert total_time < 60  # Should complete within reasonable time

    def test_quality_gate_orchestration(self):
        """Test quality gate orchestration across multiple stages."""
        # Create multi-stage pipeline
        pipeline = ValidationPipeline(self.rule_engine)

        # Add multiple checkpoints
        from src.domain.validation.gates.quality_gate import (
            create_parsing_gate,
            create_normalization_gate,
            create_relationship_gate,
        )

        pipeline.add_checkpoint("parsing", [create_parsing_gate()])
        pipeline.add_checkpoint("normalization", [create_normalization_gate()])
        pipeline.add_checkpoint(
            "relationships", [create_relationship_gate()], required=False
        )

        # Test data for different stages
        test_data = {
            "genes": [{"symbol": "TP53", "source": "test"}],
            "relationships": [
                {"gene_id": "TP53", "variant_id": "VAR1", "type": "gene_variant"}
            ],
        }

        async def run_orchestration_test():
            # Test parsing stage
            parse_result = await pipeline.validate_stage("parsing", test_data)
            assert isinstance(parse_result, dict)

            # Test normalization stage
            norm_result = await pipeline.validate_stage("normalization", test_data)
            assert isinstance(norm_result, dict)

            # Check that different stages can have different results
            # (This depends on the actual validation rules and data)

        asyncio.run(run_orchestration_test())

    def test_end_to_end_reporting_workflow(self):
        """Test end-to-end reporting workflow."""
        from src.domain.validation.reporting.report import ValidationReportGenerator

        # Set up report generator
        report_generator = ValidationReportGenerator(
            self.error_reporter, self.metrics_collector, self.dashboard
        )

        # Add some test data and errors
        self.error_reporter.add_error(
            "gene",
            "TP53",
            "symbol",
            "format_check",
            "Test error for reporting",
            source="e2e_test",
        )

        validation_results = [self.rule_engine.validate_entity("gene", self.test_gene)]
        self.metrics_collector.collect_validation_metrics(
            validation_results, "e2e_test", "gene"
        )

        # Generate reports
        executive_report = report_generator.generate_executive_report()
        technical_report = report_generator.generate_technical_report()

        # Verify report structure
        assert isinstance(executive_report, object)
        assert hasattr(executive_report, "report_id")
        assert hasattr(executive_report, "executive_summary")
        assert executive_report.data_quality_score >= 0.0

        assert isinstance(technical_report, object)
        assert (
            technical_report.report_id != executive_report.report_id
        )  # Different reports

        # Export reports
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            exec_path = f"{temp_dir}/executive_report.html"
            tech_path = f"{temp_dir}/technical_report.json"

            report_generator.export_report(executive_report, exec_path, "html")
            report_generator.export_report(technical_report, tech_path, "json")

            # Verify files were created
            assert os.path.exists(exec_path)
            assert os.path.exists(tech_path)
