# tests/test_web.py
from fastapi.testclient import TestClient
from findex.web.app import app, get_engine

client = TestClient(app)


def test_health_no_index():
    response = client.get("/health")
    assert response.status_code == 503


def test_search_with_mock_engine():
    class MockEngine:
        class MockIndex:
            doc_titles = ["doc1.txt"]
            index = {"apple": [0]}

        index = MockIndex()

        def search(self, query, scorer="bm25"):
            class Res:
                doc_path = "doc1.txt"
                score = 1.5
                snippet = "apple fruit"
            return [Res()]

    app.dependency_overrides[get_engine] = lambda: MockEngine()

    response = client.get("/health")
    assert response.status_code == 200

    response = client.get("/search?q=apple")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1

    response = client.get("/docs/nonexistent")
    assert response.status_code == 404

    app.dependency_overrides.clear()