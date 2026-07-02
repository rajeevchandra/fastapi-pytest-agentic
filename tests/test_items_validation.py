import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price validation for POST /items endpoint."""

    def test_negative_price(self):
        """Negative prices should be rejected."""
        r = client.post("/items", json={"name": "book", "price": -1})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_very_negative_price(self):
        """Very negative prices should be rejected."""
        r = client.post("/items", json={"name": "book", "price": -999.99})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_zero_price_edge_case(self):
        """Zero price should be rejected."""
        r = client.post("/items", json={"name": "book", "price": 0.0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [0.01, 1.0, 100.0, 9999.99])
    def test_valid_prices(self, price):
        """Valid positive prices should be accepted."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price


class TestCreateItemMissingFields:
    """Test missing required fields for POST /items endpoint."""

    def test_missing_name_field(self):
        """Missing name field should return 422."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_missing_price_field(self):
        """Missing price field should return 422."""
        r = client.post("/items", json={"name": "book"})
        assert r.status_code == 422

    def test_empty_payload(self):
        """Empty payload should return 422."""
        r = client.post("/items", json={})
        assert r.status_code == 422


class TestCreateItemInvalidTypes:
    """Test type validation for POST /items endpoint."""

    def test_string_price(self):
        """String price should be rejected."""
        r = client.post("/items", json={"name": "book", "price": "invalid"})
        assert r.status_code == 422

    def test_null_price(self):
        """Null price should be rejected."""
        r = client.post("/items", json={"name": "book", "price": None})
        assert r.status_code == 422

    def test_numeric_name_as_number(self):
        """Name as number should fail validation."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        assert r.status_code == 422

    def test_null_name(self):
        """Null name should be rejected."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422


class TestCreateItemNameValidation:
    """Test name field validation for POST /items endpoint."""

    def test_empty_name(self):
        """Empty string name should be accepted by FastAPI but stored."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        # FastAPI allows empty strings by default for str type
        assert r.status_code == 200
        assert r.json()["name"] == ""

    def test_whitespace_only_name(self):
        """Whitespace-only name should be accepted by FastAPI."""
        r = client.post("/items", json={"name": "   ", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "   "

    def test_very_long_name(self):
        """Very long name should be accepted."""
        long_name = "a" * 10000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_name_with_special_characters(self):
        """Name with special characters should be accepted."""
        special_name = "Book™ #1 (2024) €15.99 中文"
        r = client.post("/items", json={"name": special_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == special_name


class TestCreateItemExtremeValues:
    """Test extreme value handling for POST /items endpoint."""

    def test_very_large_price(self):
        """Very large prices should be accepted."""
        r = client.post("/items", json={"name": "luxury", "price": 1e10})
        assert r.status_code == 200
        assert r.json()["price"] == 1e10

    def test_very_small_positive_price(self):
        """Very small positive price should be accepted."""
        r = client.post("/items", json={"name": "item", "price": 0.0001})
        assert r.status_code == 200
        assert r.json()["price"] == 0.0001

    def test_scientific_notation_price(self):
        """Scientific notation for price should work."""
        r = client.post("/items", json={"name": "item", "price": 1.5e2})
        assert r.status_code == 200
        assert r.json()["price"] == 150.0


class TestCreateItemResponseStructure:
    """Test response structure for POST /items endpoint."""

    def test_response_contains_id(self):
        """Response should always contain id field."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert data["id"] == 1

    def test_response_contains_all_fields(self):
        """Response should contain name and price."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_response_preserves_input_values(self):
        """Response should preserve input name and price."""
        name = "Premium Book"
        price = 29.99
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price
