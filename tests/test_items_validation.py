"""
Enhanced input validation tests for POST /items endpoint.
Tests edge cases, boundary values, and error conditions.
"""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price validation for POST /items endpoint."""

    def test_create_item_with_positive_price(self):
        """Valid item creation with positive price."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == 12.5

    def test_create_item_with_zero_price(self):
        """Reject zero price."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_with_negative_price(self):
        """Reject negative price."""
        r = client.post("/items", json={"name": "item", "price": -5})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_with_large_negative_price(self):
        """Reject large negative price."""
        r = client.post("/items", json={"name": "item", "price": -1000000})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_with_very_small_positive_price(self):
        """Accept very small positive price."""
        r = client.post("/items", json={"name": "item", "price": 0.01})
        assert r.status_code == 200
        assert r.json()["price"] == 0.01

    def test_create_item_with_very_large_price(self):
        """Accept very large price value."""
        r = client.post("/items", json={"name": "item", "price": 999999999.99})
        assert r.status_code == 200
        assert r.json()["price"] == 999999999.99

    @pytest.mark.parametrize("price", [-100, -10, -0.1, 0])
    def test_create_item_rejects_non_positive_prices(self, price):
        """Parametrized test for all non-positive prices."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400


class TestCreateItemInputValidation:
    """Test input validation for POST /items endpoint."""

    def test_create_item_missing_name(self):
        """Reject request missing name field."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_create_item_missing_price(self):
        """Reject request missing price field."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422

    def test_create_item_missing_both_fields(self):
        """Reject request missing both fields."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_create_item_with_empty_name(self):
        """Accept empty name (Pydantic allows empty strings)."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == ""

    def test_create_item_with_whitespace_name(self):
        """Accept whitespace-only name."""
        r = client.post("/items", json={"name": "   ", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "   "

    def test_create_item_with_long_name(self):
        """Accept very long name."""
        long_name = "a" * 10000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_create_item_with_special_characters_in_name(self):
        """Accept special characters in name."""
        special_name = "Item!@#$%^&*()_+-={}[]|:;<>?,./~`"
        r = client.post("/items", json={"name": special_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == special_name

    def test_create_item_with_unicode_name(self):
        """Accept unicode characters in name."""
        unicode_name = "商品 🎉 Товар"
        r = client.post("/items", json={"name": unicode_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == unicode_name

    def test_create_item_with_price_as_string(self):
        """Reject price as string (Pydantic validation)."""
        r = client.post("/items", json={"name": "item", "price": "10.5"})
        assert r.status_code == 422

    def test_create_item_with_price_as_null(self):
        """Reject null price."""
        r = client.post("/items", json={"name": "item", "price": None})
        assert r.status_code == 422

    def test_create_item_with_name_as_number(self):
        """Accept numeric name (Pydantic will coerce to string)."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        assert r.status_code == 200

    def test_create_item_with_name_as_null(self):
        """Reject null name."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422

    def test_create_item_with_extra_fields(self):
        """Extra fields should be ignored by Pydantic."""
        r = client.post(
            "/items",
            json={"name": "item", "price": 10.0, "extra_field": "should_be_ignored"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "extra_field" not in data

    def test_create_item_with_price_infinity(self):
        """Handle infinity as price value."""
        r = client.post("/items", json={"name": "item", "price": float("inf")})
        # Depending on JSON serialization, this might fail at parsing
        # or be accepted. Either 200 or 422 is reasonable.
        assert r.status_code in [200, 422]

    def test_create_item_with_malformed_json(self):
        """Reject malformed JSON."""
        r = client.post("/items", content="{invalid json}")
        assert r.status_code == 422

    def test_create_item_response_structure(self):
        """Verify complete response structure."""
        r = client.post("/items", json={"name": "book", "price": 15.99})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert data["id"] == 1
        assert data["name"] == "book"
        assert data["price"] == 15.99
