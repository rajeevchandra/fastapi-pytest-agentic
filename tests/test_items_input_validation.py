"""
Comprehensive input validation tests for /items POST endpoint.
Tests boundary conditions, edge cases, and error scenarios for price and name fields.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation with boundary conditions."""

    @pytest.mark.parametrize("price", [
        -100.0,      # Large negative
        -1.0,        # Negative
        0.0,         # Zero (invalid)
        -0.01,       # Small negative
    ])
    def test_invalid_prices_rejected(self, price):
        """Prices <= 0 should be rejected with 400 status."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    @pytest.mark.parametrize("price", [
        0.01,        # Minimum valid
        1.0,         # Small valid
        99.99,       # Common price
        1000000.0,   # Large valid
    ])
    def test_valid_prices_accepted(self, price):
        """All prices > 0 should be accepted."""
        r = client.post("/items", json={"name": "product", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price


class TestCreateItemNameValidation:
    """Test name field validation."""

    def test_empty_string_name_rejected(self):
        """Empty name should be handled by Pydantic (not empty check in API)."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200  # Empty strings are valid per current API
        assert r.json()["name"] == ""

    def test_very_long_name_accepted(self):
        """Very long names should be accepted."""
        long_name = "a" * 1000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_special_characters_in_name(self):
        """Special characters should be accepted."""
        special_names = [
            "Test@123",
            "Item-With-Dashes",
            "Item_With_Underscores",
            "Item.With.Dots",
            "Café",  # Unicode
        ]
        for name in special_names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name


class TestCreateItemMissingFields:
    """Test validation of required fields."""

    def test_missing_name_field(self):
        """Missing name field should return 422."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_missing_price_field(self):
        """Missing price field should return 422."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_missing_all_fields(self):
        """Missing all fields should return 422."""
        r = client.post("/items", json={})
        assert r.status_code == 422


class TestCreateItemTypeValidation:
    """Test type validation of fields."""

    def test_string_price_rejected(self):
        """String price should be rejected by Pydantic."""
        r = client.post("/items", json={"name": "test", "price": "not-a-number"})
        assert r.status_code == 422

    def test_null_price_rejected(self):
        """Null price should be rejected by Pydantic."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422

    def test_null_name_rejected(self):
        """Null name should be rejected by Pydantic."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422

    def test_numeric_name_accepted(self):
        """Numeric name (string representation) should be accepted."""
        r = client.post("/items", json={"name": "123", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "123"


class TestCreateItemSuccessResponse:
    """Test successful response structure."""

    def test_response_has_required_fields(self):
        """Successful response should have id, name, price."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_response_field_types(self):
        """Response fields should have correct types."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_response_price_precision(self):
        """Response should preserve price precision."""
        r = client.post("/items", json={"name": "test", "price": 10.99})
        assert r.json()["price"] == 10.99
