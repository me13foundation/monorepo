"""
Ingestion coordinator for MED13 Resource Library.
Orchestrates parallel data ingestion from multiple biomedical sources.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import logging

from .base_ingestor import (
    BaseIngestor,
    IngestionError,
    IngestionResult,
    IngestionStatus,
)
from .clinvar_ingestor import ClinVarIngestor
from .pubmed_ingestor import PubMedIngestor
from .hpo_ingestor import HPOIngestor
from .uniprot_ingestor import UniProtIngestor


class IngestionPhase(Enum):
    """Phases of the ingestion process."""

    INITIALIZING = "initializing"
    INGESTING = "ingesting"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class IngestionTask:
    """Represents a single ingestion task."""

    source: str
    ingestor_class: Callable[[], BaseIngestor]
    parameters: Dict[str, Any]
    priority: int = 1  # Lower number = higher priority


@dataclass
class CoordinatorResult:
    """Result of coordinated ingestion across multiple sources."""

    total_sources: int
    completed_sources: int
    failed_sources: int
    total_records: int
    total_errors: int
    duration_seconds: float
    source_results: Dict[str, IngestionResult]
    start_time: datetime
    end_time: datetime
    phase: IngestionPhase


class IngestionCoordinator:
    """
    Coordinates parallel data ingestion from multiple biomedical sources.

    Manages concurrent execution of ingestors, handles dependencies between
    data sources, and aggregates results with comprehensive error handling.
    """

    def __init__(
        self,
        max_concurrent_ingestors: int = 4,
        enable_parallel: bool = True,
        progress_callback: Optional[
            Callable[[str, IngestionPhase, float], None]
        ] = None,
    ):
        self.max_concurrent_ingestors = max_concurrent_ingestors
        self.enable_parallel = enable_parallel
        self.progress_callback = progress_callback

        # Ingestion results storage
        self.results: Dict[str, IngestionResult] = {}

        # Configure logging
        self.logger = logging.getLogger(__name__)

        # Thread pool for CPU-bound operations
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_ingestors)

    async def coordinate_ingestion(
        self, tasks: List[IngestionTask], **global_params: Any
    ) -> CoordinatorResult:
        """
        Coordinate ingestion across multiple data sources.

        Args:
            tasks: List of ingestion tasks to execute
            **global_params: Parameters applied to all tasks

        Returns:
            Aggregated results from all ingestion tasks
        """
        start_time = datetime.now(UTC)

        # Update phase
        self._update_progress("all", IngestionPhase.INITIALIZING, 0.0)

        global_params_dict: Dict[str, Any] = dict(global_params)

        try:
            # Sort tasks by priority
            sorted_tasks = sorted(tasks, key=lambda t: t.priority)

            if self.enable_parallel:
                # Execute tasks in parallel with concurrency control
                results = await self._execute_parallel(sorted_tasks, global_params_dict)
            else:
                # Execute tasks sequentially
                results = await self._execute_sequential(
                    sorted_tasks, global_params_dict
                )

            # Aggregate results
            coordinator_result = self._aggregate_results(results, start_time)

            # Update final phase
            self._update_progress("all", IngestionPhase.COMPLETED, 100.0)

            return coordinator_result

        except Exception as e:
            self.logger.error(f"Ingestion coordination failed: {str(e)}")
            # Return failed result
            return CoordinatorResult(
                total_sources=len(tasks),
                completed_sources=0,
                failed_sources=len(tasks),
                total_records=0,
                total_errors=1,
                duration_seconds=(datetime.now(UTC) - start_time).total_seconds(),
                source_results={},
                start_time=start_time,
                end_time=datetime.now(UTC),
                phase=IngestionPhase.FAILED,
            )

    async def _execute_parallel(
        self, tasks: List[IngestionTask], global_params: Dict[str, Any]
    ) -> List[IngestionResult]:
        """
        Execute ingestion tasks in parallel with concurrency control.

        Args:
            tasks: Tasks to execute
            global_params: Global parameters

        Returns:
            List of ingestion results
        """
        semaphore = asyncio.Semaphore(self.max_concurrent_ingestors)
        results: List[IngestionResult] = []

        async def execute_with_semaphore(task: IngestionTask) -> IngestionResult:
            async with semaphore:
                return await self._execute_single_task(task, global_params)

        # Create tasks
        execution_tasks = [execute_with_semaphore(task) for task in tasks]

        # Execute with progress tracking
        completed = 0
        for coro in asyncio.as_completed(execution_tasks):
            result = await coro
            results.append(result)
            completed += 1

            # Update progress
            progress = (completed / len(tasks)) * 100
            self._update_progress("all", IngestionPhase.INGESTING, progress)

        return results

    async def _execute_sequential(
        self, tasks: List[IngestionTask], global_params: Dict[str, Any]
    ) -> List[IngestionResult]:
        """
        Execute ingestion tasks sequentially.

        Args:
            tasks: Tasks to execute
            global_params: Global parameters

        Returns:
            List of ingestion results
        """
        results: List[IngestionResult] = []

        for i, task in enumerate(tasks):
            result = await self._execute_single_task(task, global_params)
            results.append(result)

            # Update progress
            progress = ((i + 1) / len(tasks)) * 100
            self._update_progress("all", IngestionPhase.INGESTING, progress)

        return results

    async def _execute_single_task(
        self, task: IngestionTask, global_params: Dict[str, Any]
    ) -> IngestionResult:
        """
        Execute a single ingestion task.

        Args:
            task: Task to execute
            global_params: Global parameters

        Returns:
            Ingestion result
        """
        try:
            self.logger.info(f"Starting ingestion from {task.source}")

            # Merge task parameters with global parameters
            task_params: Dict[str, Any] = {**global_params, **task.parameters}

            # Create and execute ingestor
            ingestor_instance: BaseIngestor = task.ingestor_class()
            async with ingestor_instance as ingestor:
                result = await ingestor.ingest(**task_params)

            self.logger.info(
                f"Completed ingestion from {task.source}: "
                f"{result.records_processed} records processed, "
                f"{result.records_failed} failed"
            )

            # Store result
            self.results[task.source] = result
            return result

        except Exception as e:
            self.logger.error(f"Ingestion failed for {task.source}: {str(e)}")

            # Return failed result
            from src.models.value_objects import Provenance, DataSource

            failed_provenance = Provenance(
                source=DataSource(task.source),
                source_version=None,
                source_url=None,
                acquired_at=datetime.now(UTC),
                acquired_by="MED13-Resource-Library-Coordinator",
                processing_steps=[f"Failed ingestion: {str(e)}"],
                validation_status="failed",
                quality_score=0.0,
            )

            return IngestionResult(
                source=task.source,
                status=IngestionStatus.FAILED,
                records_processed=0,
                records_failed=1,
                data=[],
                provenance=failed_provenance,
                errors=[IngestionError(str(e), task.source)],
                duration_seconds=0.0,
                timestamp=datetime.now(UTC),
            )

    def _aggregate_results(
        self, results: List[IngestionResult], start_time: datetime
    ) -> CoordinatorResult:
        """
        Aggregate results from multiple ingestion tasks.

        Args:
            results: Individual ingestion results
            start_time: Start time of coordination

        Returns:
            Aggregated coordinator result
        """
        total_sources = len(results)
        completed_sources = sum(
            1 for r in results if r.status == IngestionStatus.COMPLETED
        )
        failed_sources = total_sources - completed_sources

        total_records = sum(r.records_processed for r in results)
        total_errors = sum(len(r.errors) for r in results)

        # Group results by source
        source_results = {r.source: r for r in results}

        return CoordinatorResult(
            total_sources=total_sources,
            completed_sources=completed_sources,
            failed_sources=failed_sources,
            total_records=total_records,
            total_errors=total_errors,
            duration_seconds=(datetime.now(UTC) - start_time).total_seconds(),
            source_results=source_results,
            start_time=start_time,
            end_time=datetime.now(UTC),
            phase=IngestionPhase.COMPLETED,
        )

    def _update_progress(
        self, source: str, phase: IngestionPhase, progress: float
    ) -> None:
        """Update progress if callback is provided."""
        if self.progress_callback:
            self.progress_callback(source, phase, progress)

    async def ingest_all_sources(
        self, gene_symbol: str = "MED13", **global_params: Any
    ) -> CoordinatorResult:
        """
        Convenience method to ingest from all available sources.

        Args:
            gene_symbol: Gene symbol to focus on (default: MED13)
            **global_params: Global parameters for all sources

        Returns:
            Coordinated ingestion result
        """
        tasks = [
            IngestionTask(
                source="clinvar",
                ingestor_class=ClinVarIngestor,
                parameters={"gene_symbol": gene_symbol},
                priority=1,  # High priority
            ),
            IngestionTask(
                source="pubmed",
                ingestor_class=PubMedIngestor,
                parameters={"query": gene_symbol},
                priority=2,  # Medium priority
            ),
            IngestionTask(
                source="hpo",
                ingestor_class=HPOIngestor,
                parameters={"med13_only": True},
                priority=3,  # Lower priority (can be large)
            ),
            IngestionTask(
                source="uniprot",
                ingestor_class=UniProtIngestor,
                parameters={"query": gene_symbol},
                priority=1,  # High priority
            ),
        ]

        return await self.coordinate_ingestion(tasks, **global_params)

    async def ingest_critical_sources_only(
        self, gene_symbol: str = "MED13", **global_params: Any
    ) -> CoordinatorResult:
        """
        Ingest only critical sources (ClinVar and UniProt) for faster execution.

        Args:
            gene_symbol: Gene symbol to focus on
            **global_params: Global parameters

        Returns:
            Coordinated ingestion result
        """
        tasks = [
            IngestionTask(
                source="clinvar",
                ingestor_class=ClinVarIngestor,
                parameters={"gene_symbol": gene_symbol},
                priority=1,
            ),
            IngestionTask(
                source="uniprot",
                ingestor_class=UniProtIngestor,
                parameters={"query": gene_symbol},
                priority=1,
            ),
        ]

        return await self.coordinate_ingestion(tasks, **global_params)

    def get_ingestion_summary(self, result: CoordinatorResult) -> Dict[str, Any]:
        """
        Generate a summary of ingestion results.

        Args:
            result: Coordinator result to summarize

        Returns:
            Summary dictionary
        """
        source_details: Dict[str, Dict[str, Any]] = {}

        for source, source_result in result.source_results.items():
            source_details[source] = {
                "status": source_result.status.name,
                "records_processed": source_result.records_processed,
                "records_failed": source_result.records_failed,
                "errors_count": len(source_result.errors),
                "duration_seconds": source_result.duration_seconds,
            }

        success_rate = (
            result.completed_sources / result.total_sources * 100
            if result.total_sources > 0
            else 0
        )
        records_per_second = (
            result.total_records / result.duration_seconds
            if result.duration_seconds > 0
            else 0
        )

        summary: Dict[str, Any] = {
            "total_sources": result.total_sources,
            "completed_sources": result.completed_sources,
            "failed_sources": result.failed_sources,
            "success_rate": success_rate,
            "total_records": result.total_records,
            "total_errors": result.total_errors,
            "duration_seconds": result.duration_seconds,
            "records_per_second": records_per_second,
            "source_details": source_details,
        }

        return summary

    async def retry_failed_sources(
        self, previous_result: CoordinatorResult, **retry_params: Any
    ) -> CoordinatorResult:
        """
        Retry ingestion for failed sources.

        Args:
            previous_result: Result from previous ingestion attempt
            **retry_params: Parameters for retry attempts

        Returns:
            New coordinated ingestion result
        """
        failed_sources: List[str] = [
            source
            for source, result in previous_result.source_results.items()
            if result.status.name == "FAILED"
        ]

        if not failed_sources:
            # No failures to retry
            return previous_result

        self.logger.info(f"Retrying {len(failed_sources)} failed sources")

        # Create retry tasks (would need to reconstruct original task parameters)
        # For now, create basic retry tasks
        retry_tasks: List[IngestionTask] = []
        for source in failed_sources:
            if source == "clinvar":
                retry_tasks.append(
                    IngestionTask(
                        source=source,
                        ingestor_class=ClinVarIngestor,
                        parameters={"gene_symbol": "MED13"},
                        priority=1,
                    )
                )
            elif source == "pubmed":
                retry_tasks.append(
                    IngestionTask(
                        source=source,
                        ingestor_class=PubMedIngestor,
                        parameters={"query": "MED13"},
                        priority=2,
                    )
                )
            elif source == "hpo":
                retry_tasks.append(
                    IngestionTask(
                        source=source,
                        ingestor_class=HPOIngestor,
                        parameters={"med13_only": True},
                        priority=3,
                    )
                )
            elif source == "uniprot":
                retry_tasks.append(
                    IngestionTask(
                        source=source,
                        ingestor_class=UniProtIngestor,
                        parameters={"query": "MED13"},
                        priority=1,
                    )
                )

        return await self.coordinate_ingestion(retry_tasks, **retry_params)
