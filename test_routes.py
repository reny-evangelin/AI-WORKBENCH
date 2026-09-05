from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

response = client.post("/chat", data={"message": "hello"})
print("Status:", response.status_code)
print("Response:", response.json())
