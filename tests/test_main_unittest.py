import unittest
from fastapi.testclient import TestClient
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from main import app

client = TestClient(app)

class TestMain(unittest.TestCase):
    def test_read_root(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("<h1>Hello from FastAPI!</h1>", response.text)

if __name__ == "__main__":
    unittest.main()
