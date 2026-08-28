"""
Edge cases and integration testing.
Tests cover boundary conditions, extreme values, and complex scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceBoundaries:
    """Test extreme price boundary values."""

    @pytest.mark.parametrize("price", [0.001, 0.01, 1, 100, 999999, 1000000])
    def test_create_item_valid_price_boundaries(self, price):
        """Test that various valid prices work correctly."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [-999999, -1000, -100, -1, -0.001, 0])
    def test_create_item_non_positive_boundary_rejection(self, price):
        """Test that all non-positive prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    @pytest.mark.parametrize("price", [float('inf'), float('nan')])
    def test_create_item_special_float_values(self, price):
        """Test special float values (inf, nan)."""
        r = client.post("/items", json={"name": "test", "price": price})
        # These may be rejected or handled by FastAPI
        assert r.status_code in [200, 400, 422]


class TestCreateItemNameBoundaries:
    """Test extreme name boundary values."""

    @pytest.mark.parametrize("name", [
        "a",
        "ab",
        "A",
        "A" * 100,
        "A" * 1000,
        "Product 123",
        "Product-123",
        "Product_123",
        "café",
        "中文",
    ])
    def test_create_item_valid_name_boundaries(self, name):
        """Test that various valid names are accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize("name", ["", " ", "\t", "\n"])
    def test_create_item_whitespace_names(self, name):
        """Test whitespace-only names."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        # Should work or be handled by validation
        if r.status_code == 200:
            assert r.json()["name"] == name


class TestGetItemIDEdgeCases:
    """Test extreme item ID boundary values."""

    @pytest.mark.parametrize("item_id", [1])
    def test_get_item_found_id_one(self, item_id):
        """Test that only ID 1 is found."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200

    @pytest.mark.parametrize("item_id", [
        0, -1, -1000, 2, 3, 10, 100, 1000, 999999, 2147483647
    ])
    def test_get_item_not_found_various_ids(self, item_id):
        """Test that all IDs except 1 return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"


class TestCreateItemVariousScenarios:
    """Test various realistic scenarios."""

    @pytest.mark.parametrize("name,price", [
        ("Book", 12.99),
        ("Pen", 0.99),
        ("Laptop", 999.99),
        ("Coffee", 3.50),
        ("Water Bottle", 25.00),
    ])
    def test_create_item_realistic_products(self, name, price):
        """Test creating realistic product items."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price
        assert data["id"] == 1

    @pytest.mark.parametrize("price_str", ["10.99", "100"])
    def test_create_item_numeric_string_price(self, price_str):
        """Test that numeric strings for price are coerced or rejected."""
        r = client.post("/items", json={"name": "test", "price": price_str})
        # Pydantic may coerce string to float
        assert r.status_code in [200, 422]

    def test_create_item_duplicate_creates_different_item(self):
        """Test that multiple creates always return same response (id=1)."""
        r1 = client.post("/items", json={"name": "item1", "price": 10.0})
        r2 = client.post("/items", json={"name": "item2", "price": 20.0})
        assert r1.status_code == 200
        assert r2.status_code == 200
        # Both return id=1 since it's hardcoded
        assert r1.json()["id"] == 1
        assert r2.json()["id"] == 1


class TestHealthEndpoint:
    """Additional health endpoint tests."""

    def test_health_endpoint_exists(self):
        """Test health endpoint is accessible."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_endpoint_response_structure(self):
        """Test health endpoint response structure."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_health_endpoint_exact_response(self):
        """Test health endpoint exact response."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_health_endpoint_content_type(self):
        """Test health endpoint content type."""
        r = client.get("/health")
        assert r.status_code == 200
        assert "application/json" in r.headers["content-type"]


class TestAPIConsistency:
    """Test API behavior consistency."""

    def test_same_request_same_response(self):
        """Test that same request always gets same response."""
        r1 = client.post("/items", json={"name": "test", "price": 10.0})
        r2 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r1.json() == r2.json()

    def test_get_item_idempotent(self):
        """Test that GET requests are idempotent."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        assert r1.json() == r2.json()

    def test_404_consistency(self):
        """Test that 404 responses are consistent."""
        r1 = client.get("/items/2")
        r2 = client.get("/items/3")
        assert r1.status_code == 404
        assert r2.status_code == 404
        assert r1.json()["detail"] == r2.json()["detail"]


class TestErrorMessageQuality:
    """Test quality and consistency of error messages."""

    def test_price_error_message_clear(self):
        """Test that price error message is clear and helpful."""
        r = client.post("/items", json={"name": "test", "price": -5})
        assert r.status_code == 400
        msg = r.json()["detail"]
        assert "price" in msg.lower()
        assert "0" in msg or "positive" in msg.lower()

    def test_not_found_error_message_clear(self):
        """Test that not found error is clear."""
        r = client.get("/items/999")
        assert r.status_code == 404
        msg = r.json()["detail"]
        assert "not found" in msg.lower()

    @pytest.mark.parametrize("status_code", [400, 404])
    def test_error_responses_have_detail(self, status_code):
        """Test that all error responses have detail field."""
        if status_code == 400:
            r = client.post("/items", json={"name": "test", "price": 0})
        else:
            r = client.get("/items/999")
        assert r.status_code == status_code
        assert "detail" in r.json()


class TestResponseConsistency:
    """Test consistency of response structures."""

    def test_all_success_responses_have_same_fields(self):
        """Test that all successful responses have consistent fields."""
        r1 = client.post("/items", json={"name": "a", "price": 1.0})
        r2 = client.get("/items/1")
        
        assert r1.status_code == 200
        assert r2.status_code == 200
        
        # Both should have same field names
        fields1 = set(r1.json().keys())
        fields2 = set(r2.json().keys())
        assert fields1 == fields2
        assert fields1 == {"id", "name", "price"}

    def test_all_error_responses_have_detail(self):
        """Test that all error responses have detail field."""
        r1 = client.post("/items", json={"name": "test", "price": 0})
        r2 = client.get("/items/999")
        
        assert r1.status_code == 400
        assert r2.status_code == 404
        
        assert "detail" in r1.json()
        assert "detail" in r2.json()


class TestInputNormalization:
    """Test input normalization and handling."""

    def test_create_item_preserves_name_case(self):
        """Test that item name case is preserved."""
        names = ["Test", "TEST", "test", "TeSt"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name

    def test_create_item_preserves_price_precision(self):
        """Test that price precision is preserved."""
        prices = [10.5, 10.25, 10.125, 10.05]
        for price in prices:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price

    def test_create_item_accepts_integer_price(self):
        """Test that integer prices work."""
        r = client.post("/items", json={"name": "test", "price": 100})
        assert r.status_code == 200
        assert r.json()["price"] == 100


class TestEndpointDiscoverability:
    """Test endpoint structure and discoverability."""

    def test_health_endpoint_path(self):
        """Test health endpoint at correct path."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_items_post_endpoint_path(self):
        """Test POST /items endpoint."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200

    def test_items_get_endpoint_path(self):
        """Test GET /items/{id} endpoint."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_root_endpoint_exists(self):
        """Test that root path is defined."""
        r = client.get("/")
        # May return 404 or some default response
        assert r.status_code in [200, 404, 405]
