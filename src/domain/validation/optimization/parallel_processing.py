"""
Parallel processing for validation performance optimization.

Provides parallel validation execution using asyncio and concurrent.futures
to improve throughput for large-scale validation operations.
"""

import asyncio
import concurrent.futures
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from ..rules.base_rules import ValidationRuleEngine, ValidationResult


class ProcessingMode(Enum):
    """Parallel processing modes."""

    ASYNCIO = "asyncio"  # Asyncio-based parallelism
    THREAD_POOL = "thread_pool"  # Thread pool executor
    PROCESS_POOL = "process_pool"  # Process pool executor
    HYBRID = "hybrid"  # Combination of thread and process pools


@dataclass
class ParallelConfig:
    """Configuration for parallel processing."""

    mode: ProcessingMode = ProcessingMode.ASYNCIO
    max_workers: int = 4
    chunk_size: int = 100
    enable_batching: bool = True
    timeout_seconds: float = 300.0
    memory_limit_mb: int = 500
    enable_progress_tracking: bool = True


class ParallelValidator:
    """
    Parallel validation processor.

    Executes validation operations in parallel to improve performance
    for large datasets and complex validation rules.
    """

    def __init__(
        self, rule_engine: ValidationRuleEngine, config: Optional[ParallelConfig] = None
    ):
        self.rule_engine = rule_engine
        self.config = config or ParallelConfig()

        # Executors for different processing modes
        self._thread_executor = None
        self._process_executor = None

        # Progress tracking
        self._progress_callback: Optional[Callable[[str, float], None]] = None

    async def validate_batch_parallel(
        self,
        entity_type: str,
        entities: List[Dict[str, Any]],
        rule_selection: Optional[List[str]] = None,
    ) -> List[ValidationResult]:
        """
        Validate a batch of entities in parallel.

        Args:
            entity_type: Type of entities to validate
            entities: List of entity data dictionaries
            rule_selection: Optional list of rules to apply

        Returns:
            List of ValidationResult objects
        """
        if not entities:
            return []

        if len(entities) <= self.config.chunk_size:
            # For small batches, use sequential processing
            return self.rule_engine.validate_batch(
                entity_type, entities, rule_selection
            )

        # Split into chunks
        chunks = self._create_chunks(entities, self.config.chunk_size)

        if self.config.mode == ProcessingMode.ASYNCIO:
            return await self._validate_asyncio(entity_type, chunks, rule_selection)
        elif self.config.mode == ProcessingMode.THREAD_POOL:
            return await self._validate_thread_pool(entity_type, chunks, rule_selection)
        elif self.config.mode == ProcessingMode.PROCESS_POOL:
            return await self._validate_process_pool(
                entity_type, chunks, rule_selection
            )
        else:  # HYBRID
            return await self._validate_hybrid(entity_type, chunks, rule_selection)

    async def validate_mixed_batch_parallel(
        self,
        entity_batches: Dict[str, List[Dict[str, Any]]],
        rule_selections: Optional[Dict[str, List[str]]] = None,
    ) -> Dict[str, List[ValidationResult]]:
        """
        Validate multiple entity types in parallel.

        Args:
            entity_batches: Dictionary mapping entity types to entity lists
            rule_selections: Optional rule selections per entity type

        Returns:
            Dictionary mapping entity types to validation result lists
        """
        tasks = []

        for entity_type, entities in entity_batches.items():
            rule_selection = (
                rule_selections.get(entity_type) if rule_selections else None
            )
            task = self.validate_batch_parallel(entity_type, entities, rule_selection)
            tasks.append((entity_type, task))

        # Execute all tasks concurrently
        results = {}
        completed_tasks = await asyncio.gather(
            *[task for _, task in tasks], return_exceptions=True
        )

        for i, (entity_type, _) in enumerate(tasks):
            if isinstance(completed_tasks[i], Exception):
                # Handle validation errors
                print(f"Validation failed for {entity_type}: {completed_tasks[i]}")
                results[entity_type] = []
            else:
                results[entity_type] = completed_tasks[i]

        return results

    def _create_chunks(
        self, entities: List[Dict[str, Any]], chunk_size: int
    ) -> List[List[Dict[str, Any]]]:
        """Split entities into chunks for parallel processing."""
        return [
            entities[i : i + chunk_size] for i in range(0, len(entities), chunk_size)
        ]

    async def _validate_asyncio(
        self,
        entity_type: str,
        chunks: List[List[Dict[str, Any]]],
        rule_selection: Optional[List[str]],
    ) -> List[ValidationResult]:
        """Validate using asyncio concurrency."""

        async def validate_chunk(chunk: List[Dict[str, Any]]) -> List[ValidationResult]:
            # Run validation in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: self.rule_engine.validate_batch(
                    entity_type, chunk, rule_selection
                ),
            )

        # Create tasks for each chunk
        tasks = [validate_chunk(chunk) for chunk in chunks]

        # Execute tasks with progress tracking
        results = []
        total_chunks = len(chunks)

        for i, task in enumerate(tasks):
            if self._progress_callback:
                progress = (i / total_chunks) * 100
                self._progress_callback(f"Validating {entity_type} chunks", progress)

            try:
                chunk_results = await asyncio.wait_for(
                    task, timeout=self.config.timeout_seconds
                )
                results.extend(chunk_results)
            except asyncio.TimeoutError:
                print(f"Validation timeout for {entity_type} chunk {i}")
                # Return error results for failed chunks
                error_results = [
                    ValidationResult(
                        is_valid=False,
                        issues=[
                            {
                                "field": "validation",
                                "rule": "timeout",
                                "severity": "error",
                                "message": f"Validation timeout after {self.config.timeout_seconds}s",
                            }
                        ],
                        score=0.0,
                    )
                ] * len(chunks[i])
                results.extend(error_results)

        return results

    async def _validate_thread_pool(
        self,
        entity_type: str,
        chunks: List[List[Dict[str, Any]]],
        rule_selection: Optional[List[str]],
    ) -> List[ValidationResult]:
        """Validate using thread pool executor."""
        if not self._thread_executor:
            self._thread_executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=self.config.max_workers
            )

        loop = asyncio.get_event_loop()

        def validate_chunk_sync(chunk: List[Dict[str, Any]]) -> List[ValidationResult]:
            return self.rule_engine.validate_batch(entity_type, chunk, rule_selection)

        # Submit all chunks to thread pool
        futures = [
            loop.run_in_executor(self._thread_executor, validate_chunk_sync, chunk)
            for chunk in chunks
        ]

        # Collect results
        results = []
        for i, future in enumerate(futures):
            if self._progress_callback:
                progress = (i / len(futures)) * 100
                self._progress_callback(f"Processing {entity_type} threads", progress)

            try:
                chunk_results = await asyncio.wait_for(
                    asyncio.wrap_future(future), timeout=self.config.timeout_seconds
                )
                results.extend(chunk_results)
            except asyncio.TimeoutError:
                print(f"Thread validation timeout for {entity_type} chunk {i}")
                error_results = [
                    ValidationResult(
                        is_valid=False,
                        issues=[
                            {
                                "field": "validation",
                                "rule": "thread_timeout",
                                "severity": "error",
                                "message": f"Thread validation timeout after {self.config.timeout_seconds}s",
                            }
                        ],
                        score=0.0,
                    )
                ] * len(chunks[i])
                results.extend(error_results)

        return results

    async def _validate_process_pool(
        self,
        entity_type: str,
        chunks: List[List[Dict[str, Any]]],
        rule_selection: Optional[List[str]],
    ) -> List[ValidationResult]:
        """Validate using process pool executor."""
        if not self._process_executor:
            self._process_executor = concurrent.futures.ProcessPoolExecutor(
                max_workers=self.config.max_workers
            )

        loop = asyncio.get_event_loop()

        # Note: Process pool requires picklable objects
        # This is a simplified implementation - in practice would need careful handling
        def validate_chunk_sync(chunk: List[Dict[str, Any]]) -> List[ValidationResult]:
            # Create a new rule engine instance for each process
            # (can't pickle the main instance)
            temp_engine = ValidationRuleEngine()
            return temp_engine.validate_batch(entity_type, chunk, rule_selection)

        # Submit all chunks to process pool
        futures = [
            loop.run_in_executor(self._process_executor, validate_chunk_sync, chunk)
            for chunk in chunks
        ]

        # Collect results
        results = []
        for i, future in enumerate(futures):
            if self._progress_callback:
                progress = (i / len(futures)) * 100
                self._progress_callback(f"Processing {entity_type} processes", progress)

            try:
                chunk_results = await asyncio.wait_for(
                    asyncio.wrap_future(future), timeout=self.config.timeout_seconds
                )
                results.extend(chunk_results)
            except asyncio.TimeoutError:
                print(f"Process validation timeout for {entity_type} chunk {i}")
                error_results = [
                    ValidationResult(
                        is_valid=False,
                        issues=[
                            {
                                "field": "validation",
                                "rule": "process_timeout",
                                "severity": "error",
                                "message": f"Process validation timeout after {self.config.timeout_seconds}s",
                            }
                        ],
                        score=0.0,
                    )
                ] * len(chunks[i])
                results.extend(error_results)

        return results

    async def _validate_hybrid(
        self,
        entity_type: str,
        chunks: List[List[Dict[str, Any]]],
        rule_selection: Optional[List[str]],
    ) -> List[ValidationResult]:
        """Validate using hybrid thread/process approach."""
        # For hybrid mode, use threads for I/O-bound operations
        # and processes for CPU-bound validation rules
        # Simplified: delegate to thread pool for now
        return await self._validate_thread_pool(entity_type, chunks, rule_selection)

    def set_progress_callback(self, callback: Callable[[str, float], None]):
        """Set progress tracking callback."""
        self._progress_callback = callback

    async def validate_with_adaptive_parallelism(
        self,
        entity_type: str,
        entities: List[Dict[str, Any]],
        rule_selection: Optional[List[str]] = None,
    ) -> List[ValidationResult]:
        """
        Validate with adaptive parallelism based on workload characteristics.

        Args:
            entity_type: Type of entities
            entities: Entity data
            rule_selection: Optional rule selection

        Returns:
            Validation results
        """
        # Analyze workload characteristics
        workload_size = len(entities)
        avg_entity_complexity = self._estimate_entity_complexity(
            entities[: min(10, len(entities))]
        )

        # Choose processing mode based on characteristics
        if workload_size < 100:
            # Small workload - sequential processing
            return self.rule_engine.validate_batch(
                entity_type, entities, rule_selection
            )
        elif workload_size < 1000 and avg_entity_complexity < 0.5:
            # Medium workload, low complexity - asyncio
            config = ParallelConfig(mode=ProcessingMode.ASYNCIO, max_workers=2)
            validator = ParallelValidator(self.rule_engine, config)
            return await validator.validate_batch_parallel(
                entity_type, entities, rule_selection
            )
        elif avg_entity_complexity > 0.7:
            # High complexity - process pool for CPU isolation
            config = ParallelConfig(
                mode=ProcessingMode.PROCESS_POOL,
                max_workers=min(4, self.config.max_workers),
            )
            validator = ParallelValidator(self.rule_engine, config)
            return await validator.validate_batch_parallel(
                entity_type, entities, rule_selection
            )
        else:
            # Default - thread pool
            config = ParallelConfig(
                mode=ProcessingMode.THREAD_POOL, max_workers=self.config.max_workers
            )
            validator = ParallelValidator(self.rule_engine, config)
            return await validator.validate_batch_parallel(
                entity_type, entities, rule_selection
            )

    def _estimate_entity_complexity(
        self, sample_entities: List[Dict[str, Any]]
    ) -> float:
        """Estimate average complexity of entities."""
        if not sample_entities:
            return 0.0

        complexities = []
        for entity in sample_entities:
            # Estimate complexity based on field count and data types
            field_count = len(entity)
            nested_objects = sum(
                1 for v in entity.values() if isinstance(v, (dict, list))
            )
            string_lengths = sum(
                len(str(v)) for v in entity.values() if isinstance(v, str)
            )

            # Normalize complexity score (0-1)
            complexity = min(
                1.0, (field_count * 0.1 + nested_objects * 0.2 + string_lengths * 0.001)
            )
            complexities.append(complexity)

        return sum(complexities) / len(complexities) if complexities else 0.0

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for parallel processing."""
        return {
            "mode": self.config.mode.value,
            "max_workers": self.config.max_workers,
            "chunk_size": self.config.chunk_size,
            "thread_pool_active": self._thread_executor is not None,
            "process_pool_active": self._process_executor is not None,
            "timeout_seconds": self.config.timeout_seconds,
        }

    def cleanup(self):
        """Clean up executors and resources."""
        if self._thread_executor:
            self._thread_executor.shutdown(wait=True)
            self._thread_executor = None

        if self._process_executor:
            self._process_executor.shutdown(wait=True)
            self._process_executor = None
