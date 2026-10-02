"""
Input validation and boundary testing for the create_item endpoint.

Tests cover:
- Price boundary conditions (negative, zero, large values)
- Name field variations (empty, special chars, long strings)
- Missing required fields
- Type validation
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price validation for create_item endpoint."""

    @pytest.mark.parametrize("price", [-100, -1, -0.01])
    def test_negative_prices_rejected(self, price):
        """Negative prices should be rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_zero_price_rejected(self):
        """Zero price should be rejected."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [0.01, 1, 10, 100.5, 1e6, 9999.99])
    def test_positive_prices_accepted(self, price):
        """All positive prices should be accepted."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price
        assert data["id"] == 1

    def test_very_large_price(self):
        """Very large prices should be accepted."""
        r = client.post("/items", json={"name": "luxury", "price": 1e10})
        assert r.status_code == 200
        assert r.json()["price"] == 1e10


class TestCreateItemNameValidation:
    """Test name field validation for create_item endpoint."""

    def test_empty_string_name_accepted(self):
        """Empty string name should be accepted (no validation)."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == ""

    def test_single_char_name(self):
        """Single character names should be accepted."""
        r = client.post("/items", json={"name": "a", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "a"

    @pytest.mark.parametrize("name", [
        "item with spaces",
        "item-with-hyphens",
        "item_with_underscores",
        "item.with.dots"
    ])
    def test_special_character_names(self, name):
        """Names with special characters should be accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_long_name_string(self):
        """Very long names should be accepted."""
        long_name = "x" * 1000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_unicode_characters_in_name(self):
        """Names with unicode characters should be accepted."""
        names = ["café", "日本語", "Ñoño", "emoji😀"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name


class TestCreateItemMissingFields:
    """Test handling of missing required fields."""

    def test_missing_name_field(self):
        """Missing name field should return 422."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_missing_price_field(self):
        """Missing price field should return 422."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_both_fields_missing(self):
        """Missing both fields should return 422."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_empty_body(self):
        """Empty body should return 422."""
        r = client.post("/items", json=None, headers={"Content-Length": "0"})
        assert r.status_code in [400, 422]


class TestCreateItemTypeValidation:
    """Test type validation for create_item fields."""

    @pytest.mark.parametrize("price", ["10", "10.5", "string"])
    def test_string_price_rejected(self, price):
        """String price should be rejected (type error)."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 422

    @pytest.mark.parametrize("name", [1, 10.5, True, None])
    def test_non_string_name(self, name):
        """Non-string names might be accepted (depends on pydantic coercion)."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        # Pydantic may coerce these to strings or reject with 422
        assert r.status_code in [200, 422]


class TestCreateItemResponseStructure:
    """Test response structure from create_item."""

    def test_response_has_required_fields(self):
        """Response should have id, name, and price fields."""
        r = client.post("/items", json={"name": "book", "price": 15.5})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_response_field_types(self):
        """Response fields should have correct types."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_response_preserves_input_values(self):
        """Response should preserve input name and price values."""
        test_name = "special-item"
        test_price = 99.99
        r = client.post("/items", json={"name": test_name, "price": test_price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == test_name
        assert data["price"] == test_price


class TestCreateItemErrorMessages:
    """Test error message consistency."""

    def test_price_error_detail_message(self):
        """Price validation error should have clear detail message."""
        r = client.post("/items", json={"name": "test", "price": -5})
        assert r.status_code == 400
        assert "detail" in r.json()
        assert "price" in r.json()["detail"].lower()
        assert "0" in r.json()["detail"]
