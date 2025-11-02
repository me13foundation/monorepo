"""Utility helpers to generate deterministic sample data for tests."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class SyntheticDataset:
    data: List[Dict[str, Any]]


class TestDataGenerator:
    def __init__(self, seed: int | None = None) -> None:
        self._random = random.Random(seed)

    def generate_gene_dataset(self, count: int, quality: str) -> SyntheticDataset:
        records: List[Dict[str, Any]] = []
        for index in range(count):
            if quality == "poor":
                record: Dict[str, Any] = {
                    "symbol": f"gene{index}",  # lower-case to trigger validation error
                    "source": "test",
                    "confidence_score": -0.5,
                }
            else:
                record = {
                    "symbol": f"GENE{index}",
                    "source": "test",
                    "confidence_score": 0.85,
                }
                if quality in {"good", "mixed"}:
                    record["hgnc_id"] = f"HGNC:{1000 + index}"
            records.append(record)

        if quality == "mixed" and records:
            records[0]["symbol"] = "invalid"
            records[0]["confidence_score"] = 1.5

        return SyntheticDataset(data=records)


setattr(TestDataGenerator, "__test__", False)

__all__ = ["SyntheticDataset", "TestDataGenerator"]
