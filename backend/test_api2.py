from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_routes():
    # Print all registered routes to see what exists
    for route in app.routes:
        if hasattr(route, "path") and "/practice/start" in route.path:
            print("FOUND ROUTE:", route.path, route.methods)

test_routes()
