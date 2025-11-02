from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ItemsApproved:
    ids: Sequence[int]


@dataclass(frozen=True)
class ItemsRejected:
    ids: Sequence[int]


@dataclass(frozen=True)
class ItemsQuarantined:
    ids: Sequence[int]


__all__ = ["ItemsApproved", "ItemsRejected", "ItemsQuarantined"]
