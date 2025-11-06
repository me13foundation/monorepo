from fastapi.testclient import TestClient

from src.database.session import engine
from src.main import create_app
from src.models.database.base import Base


def test_curation_submit_list_approve_comment(tmp_path):
    app = create_app()
    client = TestClient(app)

    # Ensure tables exist for the test
    Base.metadata.create_all(engine)

    # Submit a record for review
    resp = client.post(
        "/curation/submit",
        json={"entity_type": "genes", "entity_id": "GENE1", "priority": "high"},
    )
    assert resp.status_code == 201
    created_id = resp.json()["id"]
    assert isinstance(created_id, int)

    # List queue and ensure our item appears
    resp = client.get(
        "/curation/queue",
        params={"entity_type": "genes", "status": "pending"},
    )
    assert resp.status_code == 200
    items = resp.json()
    assert any(item["id"] == created_id for item in items)

    # Approve the item
    resp = client.post(
        "/curation/bulk",
        json={"ids": [created_id], "action": "approve"},
    )
    assert resp.status_code == 200
    assert resp.json()["updated"] >= 1

    # Leave a comment
    resp = client.post(
        "/curation/comment",
        json={
            "entity_type": "genes",
            "entity_id": "GENE1",
            "comment": "Looks good",
            "user": "tester",
        },
    )
    assert resp.status_code == 201
    assert isinstance(resp.json()["id"], int)
