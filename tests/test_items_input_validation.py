"""Input validation and boundary testing for item creation."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation with boundary values."""

    @pytest.mark.parametrize("price,should_pass", [
        (0.01, True),    # Minimum positive
        (0.1, True),     # Small valid
        (1.0, True),     # Standard price
        (100.0, True),   # Large price
        (999999.99, True),  # Very large price
        (-0.01, False),  # Negative small
        (-1.0, False),   # Negative standard
        (-100.0, False), # Negative large
        (0, False),      # Zero (invalid)
    ])
    def test_create_item_price_boundaries(self, price, should_pass):
        """Test price validation with various boundary values."""
        r = client.post("/items", json={"name": "test", "price": price})
        if should_pass:
            assert r.status_code == 200
            data = r.json()
            assert data["price"] == price
        else:
            assert r.status_code == 400
            assert "price must be > 0" in r.json()["detail"]


class TestCreateItemNameValidation:
    """Test name field validation with various formats."""

    @pytest.mark.parametrize("name", [
        "a",                          # Single character
        "Book",                       # Standard name
        "UPPERCASE",                  # All caps
        "name_with_underscore",       # With underscore
        "name-with-dash",             # With dash
        "name with spaces",           # With spaces
        "123",                        # Numbers only
        "Special!@#$%",              # Special characters
        "x" * 100,                   # Very long string
    ])
    def test_create_item_name_formats(self, name):
        """Test that various name formats are accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name


class TestCreateItemMissingFields:
    """Test validation when required fields are missing."""

    def test_missing_name(self):
        """Test error when name field is missing."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422  # Pydantic validation error

    def test_missing_price(self):
        """Test error when price field is missing."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422  # Pydantic validation error

    def test_empty_payload(self):
        """Test error with empty JSON payload."""
        r = client.post("/items", json={})
        assert r.status_code == 422  # Pydantic validation error

    def test_null_name(self):
        """Test error when name is null."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422  # Pydantic validation error

    def test_null_price(self):
        """Test error when price is null."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422  # Pydantic validation error


class TestCreateItemTypeValidation:
    """Test type validation and coercion."""

    def test_price_as_string_numeric(self):
        """Test that numeric string prices are coerced."""
        r = client.post("/items", json={"name": "test", "price": "10.5"})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == 10.5

    def test_price_as_string_non_numeric(self):
        """Test that non-numeric string prices fail."""
        r = client.post("/items", json={"name": "test", "price": "abc"})
        assert r.status_code == 422  # Type validation error

    def test_price_as_integer(self):
        """Test that integer prices are coerced to float."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == 10.0

    def test_extra_fields(self):
        """Test that extra fields are ignored."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "extra_field": "ignored",
            "another_field": 123
        })
        assert r.status_code == 200
        data = r.json()
        assert "extra_field" not in data
        assert "another_field" not in data


class TestCreateItemEdgeCases:
    """Test edge cases and unusual scenarios."""

    def test_very_small_price(self):
        """Test very small but valid price."""
        r = client.post("/items", json={"name": "test", "price": 0.001})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == 0.001

    def test_very_large_price(self):
        """Test very large but valid price."""
        r = client.post("/items", json={"name": "test", "price": 1e10})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == 1e10

    def test_name_with_unicode(self):
        """Test name with unicode characters."""
        r = client.post("/items", json={"name": "café", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "café"

    def test_name_with_emoji(self):
        """Test name with emoji characters."""
        r = client.post("/items", json={"name": "book 📚", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "book 📚"

    def test_sequential_creates(self):
        """Test multiple sequential create requests."""
        for i in range(5):
            r = client.post("/items", json={"name": f"item_{i}", "price": float(i + 1)})
            assert r.status_code == 200
            data = r.json()
            assert data["name"] == f"item_{i}"
