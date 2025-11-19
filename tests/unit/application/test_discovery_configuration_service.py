from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.application.services.discovery_configuration_requests import (
    CreatePubmedPresetRequest,
)
from src.application.services.discovery_configuration_service import (
    DiscoveryConfigurationService,
)
from src.domain.entities.data_discovery_parameters import AdvancedQueryParameters
from src.domain.entities.discovery_preset import (
    DiscoveryPreset,
    DiscoveryProvider,
    PresetScope,
)


class InMemoryPresetRepository:
    def __init__(self):
        self._presets: dict[str, DiscoveryPreset] = {}

    def create(self, preset: DiscoveryPreset) -> DiscoveryPreset:
        self._presets[str(preset.id)] = preset
        return preset

    def update(self, preset: DiscoveryPreset) -> DiscoveryPreset:  # pragma: no cover
        self._presets[str(preset.id)] = preset
        return preset

    def delete(self, preset_id, owner_id):
        preset = self._presets.get(str(preset_id))
        if preset and preset.owner_id == owner_id:
            del self._presets[str(preset_id)]
            return True
        return False

    def get_owned_preset(self, preset_id, owner_id):  # pragma: no cover
        preset = self._presets.get(str(preset_id))
        if preset and preset.owner_id == owner_id:
            return preset
        return None

    def list_for_owner(self, owner_id):
        return [
            preset for preset in self._presets.values() if preset.owner_id == owner_id
        ]

    def list_for_space(self, space_id):
        return [
            preset
            for preset in self._presets.values()
            if preset.research_space_id == space_id
            and preset.scope == PresetScope.SPACE
        ]


@pytest.fixture
def service_and_repo():
    repo = InMemoryPresetRepository()
    service = DiscoveryConfigurationService(repo)
    return service, repo


def test_create_pubmed_preset(service_and_repo):
    service, _ = service_and_repo
    owner_id = uuid4()
    request = CreatePubmedPresetRequest(
        name="Recent Trials",
        description=None,
        scope=PresetScope.USER,
        parameters=AdvancedQueryParameters(
            gene_symbol="MED13",
            search_term="cardiac",
        ),
    )

    preset = service.create_pubmed_preset(owner_id, request)
    assert preset.owner_id == owner_id
    assert preset.provider == DiscoveryProvider.PUBMED
    assert preset.metadata["query_preview"]


def test_list_pubmed_presets_combines_scopes(service_and_repo):
    service, repo = service_and_repo
    owner_id = uuid4()
    space_id = uuid4()
    now = datetime.now(UTC)
    repo._presets = {
        "user": DiscoveryPreset(
            id=uuid4(),
            owner_id=owner_id,
            provider=DiscoveryProvider.PUBMED,
            scope=PresetScope.USER,
            name="User preset",
            description=None,
            parameters=AdvancedQueryParameters(gene_symbol="MED13"),
            metadata={},
            research_space_id=None,
            created_at=now,
            updated_at=now,
        ),
        "space": DiscoveryPreset(
            id=uuid4(),
            owner_id=uuid4(),
            provider=DiscoveryProvider.PUBMED,
            scope=PresetScope.SPACE,
            name="Shared preset",
            description=None,
            parameters=AdvancedQueryParameters(search_term="cardiac"),
            metadata={},
            research_space_id=space_id,
            created_at=now,
            updated_at=now,
        ),
    }

    presets = service.list_pubmed_presets(owner_id, research_space_id=space_id)
    assert len(presets) == 2
