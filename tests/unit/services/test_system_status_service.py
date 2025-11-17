from __future__ import annotations

from uuid import uuid4

import pytest

from src.application.services.system_status_service import SystemStatusService
from src.domain.repositories.system_status_repository import SystemStatusRepository
from src.type_definitions.system_status import (
    EnableMaintenanceRequest,
    MaintenanceModeState,
)


class InMemoryStatusRepository(SystemStatusRepository):
    def __init__(self) -> None:
        self.state = MaintenanceModeState()

    def get_maintenance_state(self) -> MaintenanceModeState:
        return self.state

    def save_maintenance_state(
        self,
        state: MaintenanceModeState,
    ) -> MaintenanceModeState:
        self.state = state
        return self.state


class StubSessionRevoker:
    def __init__(self) -> None:
        self.calls: list[set[str]] = []

    def revoke_all(self, *, exclude_user_ids: set[str] | None = None) -> int:
        self.calls.append(exclude_user_ids or set())
        return 1


@pytest.mark.asyncio
async def test_enable_maintenance_revokes_sessions() -> None:
    repo = InMemoryStatusRepository()
    revoker = StubSessionRevoker()
    service = SystemStatusService(repo, revoker)

    actor_id = uuid4()
    state = await service.enable_maintenance(
        EnableMaintenanceRequest(message="Updating storage", force_logout_users=True),
        actor_id=actor_id,
        exclude_user_ids=[actor_id],
    )

    assert state.is_active is True
    assert revoker.calls == [{actor_id}]


@pytest.mark.asyncio
async def test_require_active_raises_when_disabled() -> None:
    repo = InMemoryStatusRepository()
    revoker = StubSessionRevoker()
    service = SystemStatusService(repo, revoker)

    with pytest.raises(PermissionError):
        await service.require_active()
