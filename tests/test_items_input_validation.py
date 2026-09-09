"""
Comprehensive input validation tests for POST /items endpoint.
Tests price boundaries, name variations, missing fields, and type validation.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation for POST /items."""

    @pytest.mark.parametrize("price", [0, -1, -100.5, -0.01])
    def test_create_item_rejects_non_positive_prices(self, price):
        """Price must be > 0."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [0.01, 1, 10.5, 99999.99])
    def test_create_item_accepts_positive_prices(self, price):
        """Positive prices should be accepted."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price

    def test_create_item_price_string_coercion(self):
        """Pydantic auto-coerces string to float."""
        r = client.post("/items", json={"name": "test", "price": "12.5"})
        assert r.status_code == 200
        assert r.json()["price"] == 12.5

    def test_create_item_price_int_coercion(self):
        """Pydantic auto-coerces int to float."""
        r = client.post("/items", json={"name": "test", "price": 5})
        assert r.status_code == 200
        assert r.json()["price"] == 5.0


class TestCreateItemNameValidation:
    """Test name field validation for POST /items."""

    def test_create_item_with_valid_name(self):
        """Normal names should work."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "book"

    def test_create_item_with_empty_name(self):
        """Empty name should be accepted by Pydantic (it's a valid string)."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == ""

    def test_create_item_with_long_name(self):
        """Very long names should be accepted."""
        long_name = "a" * 500
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_create_item_with_special_chars(self):
        """Names with special characters should be accepted."""
        r = client.post("/items", json={"name": "café-book™", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "café-book™"

    def test_create_item_with_whitespace_name(self):
        """Whitespace-only names should be accepted."""
        r = client.post("/items", json={"name": "   ", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "   "

    def test_create_item_name_numeric_string(self):
        """Numeric strings as names should work."""
        r = client.post("/items", json={"name": "12345", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "12345"


class TestCreateItemMissingFields:
    """Test missing required fields validation."""

    def test_create_item_missing_price(self):
        """Missing price field should return 422 validation error."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_create_item_missing_name(self):
        """Missing name field should return 422 validation error."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_create_item_missing_all_fields(self):
        """Missing all required fields should return 422."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_create_item_null_price(self):
        """Null price should return 422 validation error."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422

    def test_create_item_null_name(self):
        """Null name should return 422 validation error."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422


class TestCreateItemInvalidTypes:
    """Test invalid data type handling."""

    def test_create_item_price_invalid_string(self):
        """Non-numeric string price should fail validation."""
        r = client.post("/items", json={"name": "test", "price": "abc"})
        assert r.status_code == 422

    def test_create_item_price_list(self):
        """List as price should fail validation."""
        r = client.post("/items", json={"name": "test", "price": [10]})
        assert r.status_code == 422

    def test_create_item_price_dict(self):
        """Dict as price should fail validation."""
        r = client.post("/items", json={"name": "test", "price": {"amount": 10}})
        assert r.status_code == 422

    def test_create_item_name_number(self):
        """Numbers are auto-coerced to strings."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "123"

    def test_create_item_name_list(self):
        """List as name should fail validation."""
        r = client.post("/items", json={"name": ["book"], "price": 10.0})
        assert r.status_code == 422


class TestCreateItemExtraFields:
    """Test behavior with extra/unknown fields."""

    def test_create_item_with_extra_fields(self):
        """Extra fields should be ignored by default."""
        r = client.post("/items", json={"name": "test", "price": 10.0, "extra": "value"})
        assert r.status_code == 200
        assert r.json()["name"] == "test"
        assert r.json()["price"] == 10.0


class TestCreateItemResponseStructure:
    """Test response structure and content."""

    def test_create_item_response_fields(self):
        """Response should include id, name, and price."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_types(self):
        """Response fields should have correct types."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_create_item_id_always_one(self):
        """API always returns id=1 (simulated behavior)."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.json()["id"] == 1

    def test_create_item_response_matches_request(self):
        """Response name and price should match request."""
        req_name = "my book"
        req_price = 25.50
        r = client.post("/items", json={"name": req_name, "price": req_price})
        data = r.json()
        assert data["name"] == req_name
        assert data["price"] == req_price


class TestCreateItemEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_create_item_very_large_price(self):
        """Very large prices should be accepted."""
        r = client.post("/items", json={"name": "test", "price": 1e10})
        assert r.status_code == 200
        assert r.json()["price"] == 1e10

    def test_create_item_very_small_positive_price(self):
        """Very small positive prices should be accepted."""
        r = client.post("/items", json={"name": "test", "price": 0.0001})
        assert r.status_code == 200
        assert r.json()["price"] == 0.0001

    def test_create_item_scientific_notation_price(self):
        """Scientific notation for price should work."""
        r = client.post("/items", json={"name": "test", "price": 1.5e2})
        assert r.status_code == 200
        assert r.json()["price"] == 150.0

    def test_create_item_unicode_name(self):
        """Unicode names should work."""
        r = client.post("/items", json={"name": "📚 书籍", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "📚 书籍"
