"""Test input validation for POST /items endpoint."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price validation for create item endpoint."""

    def test_create_item_positive_price(self):
        """Test that valid positive price is accepted."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == 12.5

    def test_create_item_zero_price(self):
        """Test that zero price is rejected."""
        r = client.post("/items", json={"name": "bad", "price": 0})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_create_item_negative_price(self):
        """Test that negative price is rejected."""
        r = client.post("/items", json={"name": "bad", "price": -1})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_create_item_large_negative_price(self):
        """Test that large negative price is rejected."""
        r = client.post("/items", json={"name": "bad", "price": -100.50})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    @pytest.mark.parametrize(
        "price",
        [0, -1, -100, -0.01, -999.99],
    )
    def test_create_item_invalid_prices(self, price):
        """Test that various invalid prices are rejected."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    @pytest.mark.parametrize(
        "price",
        [0.01, 1, 10.5, 100, 999.99],
    )
    def test_create_item_valid_prices(self, price):
        """Test that various valid prices are accepted."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price


class TestCreateItemMissingFields:
    """Test missing required fields validation."""

    def test_create_item_missing_name(self):
        """Test that missing name field is rejected."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_create_item_missing_price(self):
        """Test that missing price field is rejected."""
        r = client.post("/items", json={"name": "book"})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_create_item_missing_both_fields(self):
        """Test that missing both fields is rejected."""
        r = client.post("/items", json={})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data


class TestCreateItemDataTypeValidation:
    """Test data type validation for item fields."""

    def test_create_item_string_price(self):
        """Test that string price is rejected."""
        r = client.post("/items", json={"name": "book", "price": "10.5"})
        assert r.status_code == 422

    def test_create_item_null_price(self):
        """Test that null price is rejected."""
        r = client.post("/items", json={"name": "book", "price": None})
        assert r.status_code == 422

    def test_create_item_null_name(self):
        """Test that null name is rejected."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422

    def test_create_item_integer_price(self):
        """Test that integer price is accepted."""
        r = client.post("/items", json={"name": "book", "price": 10})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == 10


class TestCreateItemNameValidation:
    """Test name field validation."""

    def test_create_item_empty_name(self):
        """Test that empty name string is accepted (no validation for empty)."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == ""

    def test_create_item_whitespace_name(self):
        """Test that whitespace-only name is accepted."""
        r = client.post("/items", json={"name": "   ", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "   "

    def test_create_item_long_name(self):
        """Test that long name is accepted."""
        long_name = "a" * 1000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == long_name

    def test_create_item_special_chars_name(self):
        """Test that special characters in name are accepted."""
        r = client.post("/items", json={"name": "Book!@#$%^&*()", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Book!@#$%^&*()"

    def test_create_item_unicode_name(self):
        """Test that unicode characters in name are accepted."""
        r = client.post("/items", json={"name": "书籍 📚", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "书籍 📚"


class TestCreateItemExtraFields:
    """Test handling of extra fields in request."""

    def test_create_item_extra_field(self):
        """Test that extra fields are ignored."""
        r = client.post(
            "/items",
            json={"name": "book", "price": 10.0, "extra_field": "ignored"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "extra_field" not in data

    def test_create_item_multiple_extra_fields(self):
        """Test that multiple extra fields are ignored."""
        r = client.post(
            "/items",
            json={
                "name": "book",
                "price": 10.0,
                "field1": "value1",
                "field2": "value2",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert "field1" not in data
        assert "field2" not in data


class TestCreateItemResponseStructure:
    """Test response structure from create item endpoint."""

    def test_create_item_response_fields(self):
        """Test that response contains all expected fields."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_id_type(self):
        """Test that response id is an integer."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)

    def test_create_item_response_name_type(self):
        """Test that response name is a string."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["name"], str)

    def test_create_item_response_price_type(self):
        """Test that response price is a number."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["price"], (int, float))


class TestCreateItemContentType:
    """Test content type handling."""

    def test_create_item_json_content_type(self):
        """Test that JSON content type is handled correctly."""
        r = client.post(
            "/items",
            json={"name": "book", "price": 10.0},
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 200

    def test_create_item_malformed_json(self):
        """Test that malformed JSON is rejected."""
        r = client.post(
            "/items",
            content="{invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 422
