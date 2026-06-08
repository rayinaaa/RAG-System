from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_rejects_empty_message():
    response = client.post("/chat", json={"message": ""})

    assert response.status_code == 422


def test_documents_endpoint_returns_list():
    response = client.get("/documents")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
