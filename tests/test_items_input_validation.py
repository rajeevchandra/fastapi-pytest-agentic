"""
Input validation tests for the items API endpoint.
Tests boundary conditions, missing fields, invalid types, and edge cases.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation and boundary conditions."""

    @pytest.mark.parametrize("price", [0, -1, -100, -0.01])
    def test_create_item_rejects_non_positive_price(self, price):
        """Price must be positive (> 0)."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [0.01, 1, 10.5, 999999.99])
    def test_create_item_accepts_positive_price(self, price):
        """Accept all positive prices."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_create_item_with_very_large_price(self):
        """Accept very large price values."""
        price = 1e10
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_create_item_with_small_decimal_price(self):
        """Accept very small positive decimal prices."""
        price = 0.0001
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price


class TestCreateItemNameValidation:
    """Test name field validation and edge cases."""

    def test_create_item_missing_name_field(self):
        """Name is required field."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_with_empty_name(self):
        """Empty string name is technically valid by Pydantic."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == ""

    @pytest.mark.parametrize("name", [
        "a",
        "very long product name with many characters",
        "Product-123",
        "Item (special)",
        "名前",  # Japanese characters
        "emoji-🎉",
    ])
    def test_create_item_with_various_names(self, name):
        """Accept various valid name formats."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_with_very_long_name(self):
        """Accept very long name strings."""
        name = "x" * 1000
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestCreateItemMissingFields:
    """Test missing required fields."""

    def test_create_item_missing_price_field(self):
        """Price is required field."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_missing_both_fields(self):
        """Missing both required fields returns validation error."""
        r = client.post("/items", json={})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_with_null_price(self):
        """Null price is invalid."""
        r = client.post("/items", json={"name": "item", "price": None})
        assert r.status_code == 422

    def test_create_item_with_null_name(self):
        """Null name is invalid."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422


class TestCreateItemInvalidTypes:
    """Test type validation for request fields."""

    def test_create_item_price_as_string_number(self):
        """Pydantic coerces string numbers to float."""
        r = client.post("/items", json={"name": "item", "price": "10.5"})
        assert r.status_code == 200
        assert r.json()["price"] == 10.5

    def test_create_item_price_as_integer(self):
        """Integer prices should be accepted."""
        r = client.post("/items", json={"name": "item", "price": 10})
        assert r.status_code == 200
        assert r.json()["price"] == 10.0

    def test_create_item_price_as_invalid_string(self):
        """Non-numeric string price fails validation."""
        r = client.post("/items", json={"name": "item", "price": "invalid"})
        assert r.status_code == 422

    def test_create_item_name_as_number(self):
        """Numeric name might be coerced to string by Pydantic."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # Pydantic may coerce this; verify response
        assert r.status_code in [200, 422]


class TestCreateItemResponseStructure:
    """Test response structure and field types."""

    def test_create_item_response_has_all_fields(self):
        """Response includes id, name, and price fields."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_id_type(self):
        """Response id should be integer."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)

    def test_create_item_response_name_type(self):
        """Response name should match request name."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["name"], str)
        assert data["name"] == "test"

    def test_create_item_response_price_type(self):
        """Response price should be numeric."""
        r = client.post("/items", json={"name": "test", "price": 10.5})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["price"], (int, float))
        assert data["price"] == 10.5


class TestCreateItemErrorHandling:
    """Test error responses and messaging."""

    def test_error_response_has_detail_field(self):
        """Error responses include detail field."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        assert "detail" in r.json()

    def test_price_error_message_content(self):
        """Price error message is clear and specific."""
        r = client.post("/items", json={"name": "item", "price": -1})
        assert r.status_code == 400
        detail = r.json()["detail"]
        assert "price" in detail.lower()
        assert "0" in detail

    @pytest.mark.parametrize("data", [
        {"price": 10.0},  # missing name
        {"name": "item"},  # missing price
        {},  # empty
    ])
    def test_validation_error_responses(self, data):
        """Validation errors return 422."""
        r = client.post("/items", json=data)
        assert r.status_code == 422
        assert "detail" in r.json()
