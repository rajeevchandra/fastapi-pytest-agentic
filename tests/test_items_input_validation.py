"""Enhanced input validation tests for POST /items endpoint."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation for create item endpoint."""

    @pytest.mark.parametrize("price", [
        0,           # Zero price
        -1,          # Negative price
        -100.5,      # Large negative price
        -0.01,       # Small negative price
    ])
    def test_create_item_rejects_non_positive_prices(self, price):
        """Test that non-positive prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    @pytest.mark.parametrize("price", [
        0.01,        # Very small positive
        1.0,         # Integer-like float
        999.99,      # Normal price
        100000.50,   # Large price
        1e10,        # Very large price
    ])
    def test_create_item_accepts_valid_prices(self, price):
        """Test that positive prices are accepted."""
        r = client.post("/items", json={"name": "valid", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price


class TestCreateItemInputValidation:
    """Test input field validation for create item endpoint."""

    def test_create_item_missing_price_field(self):
        """Test that missing price field returns 422 validation error."""
        r = client.post("/items", json={"name": "no price"})
        assert r.status_code == 422

    def test_create_item_missing_name_field(self):
        """Test that missing name field returns 422 validation error."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_create_item_empty_json(self):
        """Test that empty JSON returns 422 validation error."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_create_item_invalid_price_type_string(self):
        """Test that string price returns 422 validation error."""
        r = client.post("/items", json={"name": "bad", "price": "10.5"})
        assert r.status_code == 422

    def test_create_item_invalid_price_type_null(self):
        """Test that null price returns 422 validation error."""
        r = client.post("/items", json={"name": "bad", "price": None})
        assert r.status_code == 422

    def test_create_item_invalid_name_type_number(self):
        """Test that numeric name returns 422 validation error."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        assert r.status_code == 422

    def test_create_item_invalid_name_type_null(self):
        """Test that null name returns 422 validation error."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422

    @pytest.mark.parametrize("name", [
        "",          # Empty string
        " " * 100,   # Whitespace only (still valid per Pydantic)
        "a",         # Single character
        "x" * 1000,  # Very long name
    ])
    def test_create_item_various_name_lengths(self, name):
        """Test that various name lengths are accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200

    def test_create_item_extra_fields_ignored(self):
        """Test that extra fields in request are ignored."""
        r = client.post("/items", json={
            "name": "book",
            "price": 12.5,
            "extra": "field",
            "another": "field"
        })
        assert r.status_code == 200
        assert "extra" not in r.json()
        assert "another" not in r.json()

    def test_create_item_response_structure(self):
        """Test that response has correct structure."""
        r = client.post("/items", json={"name": "test", "price": 5.0})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert data["id"] == 1
        assert data["name"] == "test"
        assert data["price"] == 5.0

    def test_create_item_special_characters_in_name(self):
        """Test that special characters in name are handled."""
        special_names = ["book@store", "item#1", "product$99", "name&description"]
        for name in special_names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name

    def test_create_item_unicode_name(self):
        """Test that unicode characters in name are handled."""
        unicode_names = ["Küche", "日本語", "🎉emoji"]
        for name in unicode_names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name

    @pytest.mark.parametrize("price", [
        0.0000001,   # Very small positive
        1e-10,       # Scientific notation small
        float('inf'),  # Infinity (may be rejected by Pydantic)
    ])
    def test_create_item_boundary_prices(self, price):
        """Test boundary price values."""
        if price == float('inf'):
            # Infinity may be rejected
            r = client.post("/items", json={"name": "test", "price": price})
            # Accept both 200 and 422 as reasonable responses
            assert r.status_code in [200, 422]
        else:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 200


class TestCreateItemContentType:
    """Test content type handling."""

    def test_create_item_json_content_type(self):
        """Test that application/json content type is handled."""
        r = client.post(
            "/items",
            json={"name": "test", "price": 10.0},
            headers={"Content-Type": "application/json"}
        )
        assert r.status_code == 200

    def test_create_item_response_json_content_type(self):
        """Test that response has correct content type."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")
