"""Integration tests for the FastAPI application.

These tests verify end-to-end workflows and interactions between endpoints.
"""

from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test suite for health checks across the API."""

    def test_health_available_at_startup(self):
        """Test that health endpoint is available immediately"""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_consistent_response(self):
        """Test that health endpoint returns consistent response over time"""
        responses = [client.get("/health") for _ in range(10)]
        for r in responses:
            assert r.status_code == 200
            assert r.json()["status"] == "ok"


class TestItemCreationWorkflow:
    """Test suite for creating items with various inputs."""

    @pytest.mark.parametrize("name,price", [
        ("Book", 12.50),
        ("Pen", 1.99),
        ("Laptop", 999.99),
        ("A", 0.01),
        ("X" * 100, 50.00),
    ])
    def test_create_valid_items(self, name: str, price: float):
        """Parametrized test for creating items with different values"""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price
        assert data["id"] == 1

    @pytest.mark.parametrize("price", [0, -1, -100.50, -0.01])
    def test_reject_invalid_prices(self, price: float):
        """Parametrized test for rejecting non-positive prices"""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    @pytest.mark.parametrize("price", [0.001, 0.01, 1.0, 100.0, 9999999.99])
    def test_accept_valid_prices(self, price: float):
        """Parametrized test for accepting valid positive prices"""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price


class TestItemRetrieval:
    """Test suite for retrieving items."""

    def test_retrieve_known_item(self):
        """Test that item with ID 1 can be retrieved"""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    @pytest.mark.parametrize("item_id", [2, 3, 100, 999, 1000])
    def test_retrieve_unknown_items(self, item_id: int):
        """Parametrized test for items that don't exist"""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]

    @pytest.mark.parametrize("item_id", [-1, -100, 0])
    def test_retrieve_invalid_item_ids(self, item_id: int):
        """Parametrized test for invalid item IDs"""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404


class TestApiResponseFormats:
    """Test suite for validating API response formats."""

    def test_success_responses_are_json(self):
        """Test that successful responses are valid JSON"""
        endpoints = [
            ("/health", "GET"),
            ("/items/1", "GET"),
        ]
        for endpoint, method in endpoints:
            if method == "GET":
                r = client.get(endpoint)
            assert r.headers["content-type"] == "application/json"
            assert isinstance(r.json(), dict)

    def test_error_responses_have_detail(self):
        """Test that error responses include detail field"""
        # Test 400 error
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        assert "detail" in r.json()

        # Test 404 error
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "detail" in r.json()

    def test_item_response_data_types(self):
        """Test that item responses have correct data types"""
        r = client.post("/items", json={"name": "book", "price": 15.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], float)


class TestEdgeCasesAndBoundaries:
    """Test suite for edge cases and boundary conditions."""

    def test_create_item_with_unicode_name(self):
        """Test creating items with unicode characters in names"""
        names = ["商品", "Продукт", "🎁 Gift", "Café"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name

    def test_create_item_with_special_characters(self):
        """Test creating items with special characters in names"""
        special_names = [
            "Item #1",
            "50% Off!",
            "A&B",
            "Price: $9.99",
            "[Premium]",
        ]
        for name in special_names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name

    def test_create_item_with_very_long_name(self):
        """Test creating items with extremely long names"""
        long_name = "A" * 5000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert len(r.json()["name"]) == 5000

    def test_create_item_with_extreme_prices(self):
        """Test creating items with extreme price values"""
        prices = [0.01, 1e6, 9999999.99]
        for price in prices:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price


class TestErrorHandling:
    """Test suite for error handling and validation."""

    def test_malformed_json_request(self):
        """Test handling of malformed JSON"""
        # TestClient handles this at a higher level, but verify structure
        r = client.post("/items", json={"name": "test", "price": "invalid"})
        assert r.status_code == 422

    def test_missing_required_fields(self):
        """Test validation of missing required fields"""
        # Missing price
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        assert "detail" in r.json()

        # Missing name
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_invalid_field_types(self):
        """Test validation of invalid field types"""
        # String price
        r = client.post("/items", json={"name": "test", "price": "expensive"})
        assert r.status_code == 422

        # Numeric name (might be coerced to string, but let's test)
        r = client.post("/items", json={"name": 123, "price": 10.0})
        assert r.status_code == 422

    def test_null_fields(self):
        """Test handling of null/None fields"""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422

        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422


class TestResponseConsistency:
    """Test suite for response consistency and headers."""

    def test_all_successful_responses_include_headers(self):
        """Test that all successful responses have required headers"""
        responses = [
            client.get("/health"),
            client.get("/items/1"),
            client.post("/items", json={"name": "test", "price": 15.0}),
        ]
        for r in responses:
            assert r.status_code < 400
            assert r.headers["content-type"] == "application/json"

    def test_all_error_responses_include_headers(self):
        """Test that all error responses have required headers"""
        responses = [
            client.get("/items/999"),
            client.post("/items", json={"name": "test", "price": 0}),
            client.post("/items", json={"name": "test"}),
        ]
        for r in responses:
            assert r.status_code >= 400
            assert r.headers["content-type"] == "application/json"

    def test_status_codes_are_valid(self):
        """Test that status codes follow HTTP standards"""
        test_cases = [
            (client.get("/health"), 200),
            (client.get("/items/1"), 200),
            (client.post("/items", json={"name": "test", "price": 15.0}), 200),
            (client.get("/items/999"), 404),
            (client.post("/items", json={"name": "test", "price": 0}), 400),
            (client.post("/items", json={"name": "test"}), 422),
        ]
        for response, expected_status in test_cases:
            assert response.status_code == expected_status
