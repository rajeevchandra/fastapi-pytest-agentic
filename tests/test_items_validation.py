"""
Enhanced input validation tests for the POST /items endpoint.

These tests cover edge cases and error conditions as per the coverage improvement plan.
"""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price validation for create item endpoint."""

    def test_create_item_negative_price(self):
        """Test rejection of negative price."""
        r = client.post("/items", json={"name": "item", "price": -1})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_large_negative_price(self):
        """Test rejection of large negative price."""
        r = client.post("/items", json={"name": "item", "price": -100.50})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [-1, -0.01, -999.99])
    def test_create_item_various_negative_prices(self, price):
        """Parametrized test for various negative prices."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_zero_price(self):
        """Test rejection of zero price."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_very_small_positive_price(self):
        """Test acceptance of very small positive price."""
        r = client.post("/items", json={"name": "item", "price": 0.01})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == 0.01

    def test_create_item_very_large_price(self):
        """Test acceptance of very large price."""
        r = client.post("/items", json={"name": "expensive", "price": 999999999.99})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == 999999999.99


class TestCreateItemMissingFields:
    """Test missing required fields."""

    def test_create_item_missing_name(self):
        """Test rejection when name field is missing."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_missing_price(self):
        """Test rejection when price field is missing."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_missing_both_fields(self):
        """Test rejection when both fields are missing."""
        r = client.post("/items", json={})
        assert r.status_code == 422
        assert "detail" in r.json()


class TestCreateItemInvalidTypes:
    """Test invalid data types."""

    def test_create_item_invalid_price_type_string(self):
        """Test rejection when price is string instead of float."""
        r = client.post("/items", json={"name": "item", "price": "ten"})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_invalid_name_type_number(self):
        """Test rejection when name is number instead of string."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_invalid_name_type_boolean(self):
        """Test rejection when name is boolean."""
        r = client.post("/items", json={"name": True, "price": 10.0})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_invalid_price_type_array(self):
        """Test rejection when price is array."""
        r = client.post("/items", json={"name": "item", "price": [10.0]})
        assert r.status_code == 422
        assert "detail" in r.json()


class TestCreateItemNullValues:
    """Test null/None values."""

    def test_create_item_null_name(self):
        """Test rejection when name is null."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_null_price(self):
        """Test rejection when price is null."""
        r = client.post("/items", json={"name": "item", "price": None})
        assert r.status_code == 422
        assert "detail" in r.json()


class TestCreateItemEdgeCases:
    """Test edge cases for item creation."""

    def test_create_item_empty_name(self):
        """Test item with empty string name."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == ""

    def test_create_item_whitespace_name(self):
        """Test item with whitespace-only name."""
        r = client.post("/items", json={"name": "   ", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "   "

    def test_create_item_very_long_name(self):
        """Test item with very long name."""
        long_name = "x" * 10000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == long_name

    def test_create_item_unicode_name(self):
        """Test item with unicode characters in name."""
        r = client.post("/items", json={"name": "商品 🎉 Müller", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "商品 🎉 Müller"

    def test_create_item_special_chars_name(self):
        """Test item with special characters in name."""
        r = client.post("/items", json={"name": "item<>\"'&;", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "item<>\"'&;"

    def test_create_item_decimal_price_precision(self):
        """Test that price decimal values are preserved."""
        r = client.post("/items", json={"name": "item", "price": 19.99})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == 19.99

    def test_create_item_integer_price_converted_to_float(self):
        """Test that integer price is converted to float."""
        r = client.post("/items", json={"name": "item", "price": 15})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == 15.0


class TestCreateItemParametrized:
    """Parametrized tests for comprehensive coverage."""

    @pytest.mark.parametrize("name,price,expected_status", [
        ("book", 12.5, 200),
        ("pen", 1.0, 200),
        ("desk", 299.99, 200),
        ("lamp", 0, 400),
        ("chair", -5, 400),
    ])
    def test_create_item_parametrized(self, name, price, expected_status):
        """Parametrized test combining valid and invalid inputs."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == expected_status


class TestCreateItemExtraFields:
    """Test handling of extra fields in request."""

    def test_create_item_with_extra_fields(self):
        """Test that extra fields are ignored (Pydantic default behavior)."""
        r = client.post("/items", json={
            "name": "item",
            "price": 10.0,
            "extra_field": "should_be_ignored",
            "another_extra": 123
        })
        assert r.status_code == 200
        data = r.json()
        assert "extra_field" not in data
        assert "another_extra" not in data


class TestCreateItemResponseStructure:
    """Test response structure validation."""

    def test_create_item_response_has_required_fields(self):
        """Test that response contains all required fields."""
        r = client.post("/items", json={"name": "book", "price": 15.0})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert data["id"] == 1
        assert data["name"] == "book"
        assert data["price"] == 15.0

    def test_create_item_response_content_type(self):
        """Test that response has correct content type."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")
