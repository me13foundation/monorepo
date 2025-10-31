from fastapi.testclient import TestClient

from src.main import app


def test_list_resources_returns_seed_data() -> None:
    client = TestClient(app)
    response = client.get("/resources/")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload
    assert payload[0]["title"] == "MED13 Syndrome Foundation"
