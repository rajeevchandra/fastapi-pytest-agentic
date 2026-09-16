import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for GET /items/{item_id}."""

    @pytest.mark.parametrize("item_id", [-100, -1, 0, 1, 2, 999, 1000000])
    def test_get_item_various_integer_ids(self, item_id):
        """Should handle various integer IDs correctly."""
        r = client.get(f"/items/{item_id}")
        if item_id == 1:
            assert r.status_code == 200
        else:
            assert r.status_code == 404

    def test_get_item_negative_id_returns_404(self):
        """Negative item_id should return 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_get_item_zero_id_returns_404(self):
        """Zero item_id should return 404."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_large_id_returns_404(self):
        """Large item_id should return 404."""
        r = client.get("/items/9999999999")
        assert r.status_code == 404


class TestCreateItemConsistency:
    """Test consistency across multiple requests."""

    def test_create_multiple_items_all_return_same_id(self):
        """Multiple creates should return same ID (hardcoded to 1)."""
        ids = []
        for _ in range(5):
            r = client.post("/items", json={"name": "item", "price": 10.0})
            ids.append(r.json()["id"])
        assert all(id == 1 for id in ids)

    def test_create_item_with_different_prices_all_succeed(self):
        """Creating items with different prices should all succeed."""
        prices = [0.01, 1.0, 50.5, 100.0, 1000.0]
        for price in prices:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price

    def test_create_item_with_different_names_preserves_name(self):
        """Different names should be preserved in response."""
        names = ["apple", "book", "car", "dog", "egg"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name


class TestCreateItemEdgeCases:
    """Test edge cases for create_item endpoint."""

    def test_create_item_price_boundary_just_above_zero(self):
        """Price just above zero (0.001) should be accepted."""
        r = client.post("/items", json={"name": "item", "price": 0.001})
        assert r.status_code == 200

    def test_create_item_price_boundary_exactly_zero(self):
        """Price exactly zero should be rejected."""
        r = client.post("/items", json={"name": "item", "price": 0.0})
        assert r.status_code == 400

    def test_create_item_price_scientific_notation(self):
        """Price in scientific notation should work."""
        r = client.post("/items", json={"name": "item", "price": 1.5e2})
        assert r.status_code == 200
        assert r.json()["price"] == 150.0

    def test_create_item_name_with_newlines(self):
        """Name with newlines should be accepted."""
        r = client.post("/items", json={"name": "line1\nline2", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "line1\nline2"

    def test_create_item_name_with_tabs(self):
        """Name with tabs should be accepted."""
        r = client.post("/items", json={"name": "part1\tpart2", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "part1\tpart2"

    def test_create_item_with_json_escape_sequences_in_name(self):
        """Name with escape sequences should be handled."""
        r = client.post("/items", json={"name": "test\"quoted\"", "price": 10.0})
        assert r.status_code == 200


class TestGetItemEdgeCases:
    """Test edge cases for GET /items/{item_id}."""

    def test_get_item_1_always_returns_same_data(self):
        """Getting item 1 multiple times should return consistent data."""
        results = []
        for _ in range(3):
            r = client.get("/items/1")
            results.append(r.json())
        
        assert all(data == results[0] for data in results)

    def test_get_item_1_exact_response(self):
        """Item 1 should have exact expected values."""
        r = client.get("/items/1")
        assert r.json() == {"id": 1, "name": "sample", "price": 10.0}


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple endpoints."""

    def test_health_then_create_item(self):
        """Health check followed by create should work."""
        health = client.get("/health")
        assert health.status_code == 200
        
        create = client.post("/items", json={"name": "book", "price": 10.0})
        assert create.status_code == 200

    def test_create_then_get_item(self):
        """Create item then get item 1 should work."""
        create = client.post("/items", json={"name": "new", "price": 5.0})
        assert create.status_code == 200
        
        get = client.get("/items/1")
        assert get.status_code == 200
        assert get.json()["id"] == 1

    def test_get_nonexistent_after_create(self):
        """Getting non-existent item after create should still fail."""
        client.post("/items", json={"name": "item", "price": 10.0})
        
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_multiple_creates_and_gets(self):
        """Multiple creates and gets should work independently."""
        # Create items
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
        
        # Get existing
        r = client.get("/items/1")
        assert r.status_code == 200
        
        # Get non-existent
        r = client.get("/items/99")
        assert r.status_code == 404


class TestHTTPMethodValidation:
    """Test endpoint method validation."""

    def test_create_item_get_method_not_allowed(self):
        """GET on /items should not be allowed."""
        r = client.get("/items")
        assert r.status_code in [404, 405, 422]

    def test_get_item_post_method_not_allowed(self):
        """POST on /items/{id} should not be allowed."""
        r = client.post("/items/1", json={"name": "test", "price": 10.0})
        assert r.status_code in [404, 405]


class TestConcurrencyScenarios:
    """Test scenarios that might occur under concurrency."""

    def test_rapid_create_requests(self):
        """Rapid create requests should all succeed."""
        results = []
        for i in range(10):
            r = client.post("/items", json={"name": f"item{i}", "price": float(i) + 1})
            results.append(r.status_code)
        
        assert all(status == 200 for status in results)

    def test_rapid_get_requests(self):
        """Rapid get requests should work consistently."""
        results = []
        for i in range(10):
            r = client.get("/items/1")
            results.append(r.status_code)
        
        assert all(status == 200 for status in results)


class TestErrorHandlingConsistency:
    """Test consistency of error handling."""

    def test_all_validation_errors_have_detail(self):
        """All validation errors should include detail."""
        error_requests = [
            {"json": {"name": "item"}, "url": "/items"},  # missing price
            {"json": {"price": 10.0}, "url": "/items"},  # missing name
            {"json": {"name": "item", "price": 0}, "url": "/items"},  # bad price
            {"json": None, "url": "/items/abc"},  # invalid path param
        ]
        
        for req in error_requests[:3]:  # Skip invalid path param test
            r = client.post(req["url"], json=req["json"])
            if r.status_code >= 400:
                assert "detail" in r.json()

    def test_not_found_error_consistency(self):
        """All 404 responses should have consistent structure."""
        ids = [2, 3, 100, 9999]
        for item_id in ids:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404
            assert "detail" in r.json()
            assert r.json()["detail"] == "not found"


class TestDataPersistence:
    """Test data persistence across requests."""

    def test_item_1_exists_persistently(self):
        """Item 1 should always be retrievable."""
        for _ in range(5):
            r = client.get("/items/1")
            assert r.status_code == 200

    def test_created_items_dont_persist(self):
        """Items created via POST should not be retrievable by ID."""
        # The endpoint always returns id=1, and only item 1 exists in DB
        r = client.post("/items", json={"name": "temp", "price": 5.0})
        assert r.status_code == 200
        
        # But trying to get item 2 still fails
        r = client.get("/items/2")
        assert r.status_code == 404
