from approvaltests import verify
from fastapi.testclient import TestClient
import sys 
import os 
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from main import app

client = TestClient(app)

def test_home_response():
    response = client.get("/")
    assert response.status_code == 200
    assert "<h1>Hello from FastAPI!" in response.text  # ✅ use .text instead of .json()

