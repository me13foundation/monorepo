from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.domain.entities.source_template import (
    SourceTemplate,
    TemplateCategory,
    TemplateUIConfig,
    ValidationRule,
)
from src.domain.entities.user_data_source import SourceType
from src.routes import admin as admin_routes


def _sample_template() -> SourceTemplate:
    """Create a sample SourceTemplate for testing."""
    now = datetime.now(UTC)
    schema: dict[str, object] = {
        "type": "object",
        "properties": {"field": {"type": "string"}},
    }
    return SourceTemplate(
        id=uuid4(),
        created_by=uuid4(),
        name="Test Template",
        description="A template used for testing",
        category=TemplateCategory.RESEARCH,
        source_type=SourceType.API,
        schema_definition=schema,
        validation_rules=[
            ValidationRule(
                field="field",
                rule_type="required",
                error_message="Field is required",
            ),
        ],
        ui_config=TemplateUIConfig(),
        is_public=True,
        is_approved=True,
        approval_required=False,
        usage_count=1,
        success_rate=0.95,
        created_at=now,
        updated_at=now,
        approved_at=now,
        tags=["test"],
        version="1.0",
        compatibility_version="1.0",
    )


class StubTemplateService:
    """Simple stub for TemplateManagementService."""

    def __init__(self) -> None:
        self.templates = [_sample_template()]
        self.created_payload = None
        self.updated_payload = None

    def get_available_templates(self, user_id, skip, limit):  # noqa: D401, ANN001
        return self.templates

    def get_template(self, template_id):  # noqa: D401, ANN001
        for template in self.templates:
            if template.id == template_id:
                return template
        return None

    def create_template(self, request):  # noqa: D401, ANN001
        self.created_payload = request
        return self.templates[0]

    def update_template(self, template_id, request, user_id):  # noqa: D401, ANN001
        self.updated_payload = (template_id, request, user_id)
        return self.templates[0] if self.get_template(template_id) else None

    def delete_template(self, template_id, user_id):  # noqa: D401, ANN001
        return template_id == self.templates[0].id

    def make_template_public(self, template_id, user_id):  # noqa: D401, ANN001
        return self.templates[0] if self.get_template(template_id) else None

    def approve_template(self, template_id, approver_id):  # noqa: D401, ANN001
        return self.templates[0] if self.get_template(template_id) else None


def _test_client(service: StubTemplateService) -> TestClient:
    """Create a TestClient with dependency overrides."""
    app = FastAPI()
    app.include_router(admin_routes.router)
    app.dependency_overrides[admin_routes.get_template_service] = lambda: service
    return TestClient(app)


def test_list_templates_returns_templates() -> None:
    service = StubTemplateService()
    client = _test_client(service)

    response = client.get("/admin/templates")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["templates"][0]["name"] == "Test Template"


def test_create_template_invokes_service() -> None:
    service = StubTemplateService()
    client = _test_client(service)

    response = client.post(
        "/admin/templates",
        json={
            "name": "New Template",
            "description": "Desc",
            "category": "research",
            "source_type": "api",
            "schema_definition": {"type": "object"},
            "validation_rules": [
                {
                    "field": "name",
                    "rule_type": "required",
                    "parameters": {},
                    "error_message": "Name required",
                },
            ],
            "tags": ["alpha"],
            "is_public": True,
        },
    )

    assert response.status_code == 201
    assert service.created_payload is not None
    assert response.json()["name"] == "Test Template"


def test_get_template_not_found_returns_404() -> None:
    service = StubTemplateService()
    client = _test_client(service)

    response = client.get(f"/admin/templates/{uuid4()}")  # Non-existent ID

    assert response.status_code == 404
    assert response.json()["detail"] == "Template not found"


def test_approve_template_endpoint_returns_template() -> None:
    service = StubTemplateService()
    client = _test_client(service)
    template_id = service.templates[0].id

    response = client.post(f"/admin/templates/{template_id}/approve")

    assert response.status_code == 200
    assert response.json()["id"] == str(template_id)
