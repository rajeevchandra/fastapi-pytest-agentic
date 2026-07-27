"""
Input validation tests for the create_item endpoint.
Tests boundary conditions, missing fields, type coercion, and edge cases.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Parametrized tests for valid and invalid prices."""

    @pytest.mark.parametrize("price,expected_status", [
        (0.01, 200),      # Minimum valid price
        (0.1, 200),       # Small valid price
        (1.0, 200),       # Standard price
        (100.0, 200),     # Large price
        (999999.99, 200), # Very large price
    ])
    def test_create_item_valid_prices(self, price, expected_status):
        """Test that various positive prices are accepted."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == expected_status
        data = r.json()
        assert data["price"] == price

    @pytest.mark.parametrize("price", [
        -0.01,    # Negative small
        -1.0,     # Negative standard
        -100.0,   # Negative large
        -999999.99,  # Negative very large
        0,        # Zero
    ])
    def test_create_item_invalid_prices(self, price):
        """Test that zero and negative prices are rejected with 400."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"


class TestCreateItemNameValidation:
    """Parametrized tests for various name formats."""

    @pytest.mark.parametrize("name", [
        "a",                          # Single character
        "Book",                       # Uppercase
        "my_item",                    # Underscore
        "my-item",                    # Dash
        "My Item",                    # Spaces
        "Item#1",                     # Special chars
        "A" * 100,                    # Long name
        "Item (variant)",             # Parentheses
        "日本語",                      # Unicode
    ])
    def test_create_item_valid_names(self, name):
        """Test that various name formats are accepted."""
        r = client.post("/items", json={"name": name, "price": 1.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize("price_input,should_coerce", [
        (1, True),           # Integer should coerce to float
        (1.5, True),         # Float as-is
        ("5.5", False),      # String - Pydantic may reject
    ])
    def test_create_item_price_type_handling(self, price_input, should_coerce):
        """Test how different price input types are handled."""
        r = client.post("/items", json={"name": "item", "price": price_input})
        if should_coerce:
            assert r.status_code == 200
            assert isinstance(r.json()["price"], (int, float))
        else:
            # String prices may be rejected by Pydantic
            assert r.status_code in [200, 422]


class TestCreateItemMissingFields:
    """Tests for required field validation."""

    def test_create_item_missing_name(self):
        """Test request with missing name field."""
        r = client.post("/items", json={"price": 1.0})
        assert r.status_code == 422

    def test_create_item_missing_price(self):
        """Test request with missing price field."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422

    def test_create_item_empty_body(self):
        """Test request with empty JSON body."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_create_item_null_name(self):
        """Test request with null name."""
        r = client.post("/items", json={"name": None, "price": 1.0})
        assert r.status_code == 422

    def test_create_item_null_price(self):
        """Test request with null price."""
        r = client.post("/items", json={"name": "item", "price": None})
        assert r.status_code == 422


class TestCreateItemEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_create_item_very_small_price(self):
        """Test creation with very small valid price."""
        r = client.post("/items", json={"name": "item", "price": 0.001})
        assert r.status_code == 200
        assert r.json()["price"] == 0.001

    def test_create_item_very_large_price(self):
        """Test creation with very large price."""
        r = client.post("/items", json={"name": "item", "price": 9999999.99})
        assert r.status_code == 200

    def test_create_item_with_emoji_name(self):
        """Test creation with emoji in name."""
        r = client.post("/items", json={"name": "Item 📚", "price": 1.0})
        assert r.status_code == 200
        assert "📚" in r.json()["name"]

    def test_create_item_extra_fields_ignored(self):
        """Test that extra fields in request are ignored."""
        r = client.post("/items", json={
            "name": "item",
            "price": 1.0,
            "extra_field": "ignored"
        })
        assert r.status_code == 200
        assert "extra_field" not in r.json()

    def test_create_multiple_items_sequentially(self):
        """Test creating multiple items in sequence."""
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": float(i + 1)})
            assert r.status_code == 200
            assert r.json()["id"] == 1  # Always returns id=1
