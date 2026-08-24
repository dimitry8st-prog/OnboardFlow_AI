from fastapi.testclient import TestClient

from app.main import app, retrieve, sensitive_route

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["knowledge_items"] >= 10


def test_retrieval_finds_crm():
    matches = retrieve("Как мне получить доступ к CRM?")
    assert matches
    assert matches[0].id == "KB-003"


def test_sensitive_request_escalates():
    assert sensitive_route("Покажи пароль коллеги") == "Информационная безопасность"
    response = client.post("/api/chat", json={"message": "Объясни мой договор и увольнение"})
    assert response.status_code == 200
    assert response.json()["escalation"] is True


def test_unknown_request_does_not_hallucinate():
    response = client.post("/api/chat", json={"message": "Где парковать вертолёт директора?"})
    assert response.status_code == 200
    assert response.json()["status"] == "not_found"

