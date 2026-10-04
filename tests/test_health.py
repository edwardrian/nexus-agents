from fastapi.testclient import TestClient

from app.main import app

# Sin "with": no se ejecuta el lifespan, así que no intenta conectarse a Supabase
client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"



def test_swagger_docs():
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()
    assert "/api/v1/chat/sessions/{session_id}/history" in schema["paths"]
