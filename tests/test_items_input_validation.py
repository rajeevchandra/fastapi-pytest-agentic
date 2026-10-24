"""
Input Validation Tests for /items endpoint.
Tests for price boundaries, name validation, and invalid inputs.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemValidPrice:
    """Test create_item with valid prices."""

    @pytest.mark.parametrize("price,name", [
        (0.01, "minimum_valid"),
        (1.0, "small_item"),
        (10.0, "medium_item"),
        (100.0, "expensive_item"),
        (999999.99, "very_expensive"),
        (1e6, "million_price"),
        (0.001, "micro_price"),
    ])
    def test_create_item_valid_prices(self, price, name):
        """Test create_item accepts various valid positive prices."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == name
        assert data["price"] == price


class TestCreateItemInvalidPrice:
    """Test create_item with invalid prices."""

    @pytest.mark.parametrize("price", [
        0,
        -1,
        -0.01,
        -100.0,
        -999999.99,
    ])
    def test_create_item_non_positive_price(self, price):
        """Test create_item rejects zero and negative prices."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"


class TestCreateItemNameValidation:
    """Test create_item with various name inputs."""

    @pytest.mark.parametrize("name", [
        "a",
        "A",
        "1",
        "item-name",
        "item_name",
        "item.name",
        "Item Name",
        "UPPERCASE",
        "lowercase",
        "MixedCase",
        "123",
        "item 123",
        "item-123_name.test",
    ])
    def test_create_item_valid_names(self, name):
        """Test create_item accepts various valid name formats."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == name
        assert data["price"] == 10.0

    @pytest.mark.parametrize("name", [
        "",
        " ",
        "  \t  ",
    ])
    def test_create_item_empty_name(self, name):
        """Test create_item accepts empty/whitespace names (no validation)."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name

    @pytest.mark.parametrize("name", [
        "🎉 party item",
        "café",
        "naïve",
        "日本語",
        "中文",
        "العربية",
        "Ελληνικά",
        "Русский",
    ])
    def test_create_item_unicode_names(self, name):
        """Test create_item accepts unicode characters in names."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name


class TestCreateItemMissingFields:
    """Test create_item with missing required fields."""

    def test_create_item_missing_price(self):
        """Test create_item rejects missing price field."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_create_item_missing_name(self):
        """Test create_item rejects missing name field."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_create_item_empty_json(self):
        """Test create_item rejects empty JSON."""
        r = client.post("/items", json={})
        assert r.status_code == 422


class TestCreateItemInvalidTypes:
    """Test create_item with invalid data types."""

    def test_create_item_price_as_string(self):
        """Test create_item rejects non-numeric price."""
        r = client.post("/items", json={"name": "test", "price": "not_a_number"})
        assert r.status_code == 422

    def test_create_item_price_as_null(self):
        """Test create_item rejects null price."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422

    def test_create_item_name_as_number(self):
        """Test create_item accepts numeric name (coerced to string)."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # FastAPI may coerce or reject this
        assert r.status_code in [200, 422]

    def test_create_item_name_as_null(self):
        """Test create_item rejects null name."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422

    def test_create_item_extra_fields(self):
        """Test create_item ignores extra fields."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "extra_field": "should_be_ignored",
            "another": 123
        })
        assert r.status_code == 200
        data = r.json()
        assert "extra_field" not in data
        assert "another" not in data


class TestCreateItemLongNames:
    """Test create_item with very long names."""

    def test_create_item_long_name_500_chars(self):
        """Test create_item accepts long names."""
        long_name = "a" * 500
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == long_name

    def test_create_item_very_long_name_10000_chars(self):
        """Test create_item with very long name."""
        very_long_name = "x" * 10000
        r = client.post("/items", json={"name": very_long_name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == very_long_name


class TestCreateItemFloatPrecision:
    """Test create_item with various float precision cases."""

    @pytest.mark.parametrize("price", [
        0.1,
        0.01,
        0.001,
        0.0001,
        1.5,
        1.25,
        1.125,
        1.0625,
        3.14159,
    ])
    def test_create_item_float_precision(self, price):
        """Test create_item preserves float precision."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price


class TestCreateItemSpecialCharacters:
    """Test create_item with special characters in names."""

    @pytest.mark.parametrize("name", [
        "item!",
        "item@home",
        "item#1",
        "item$price",
        "item%discount",
        "item^power",
        "item&accessories",
        "item*premium",
        "item(limited)",
        "item)",
        "item-edition",
        "item_edition",
        "item+extra",
        "item=equal",
        "item[bracket]",
        "item{brace}",
        "item|pipe",
        "item\\slash",
        "item/path",
        "item:colon",
        "item;semicolon",
        "item'quote",
        'item"doublequote',
        "item<less",
        "item>greater",
        "item.dot",
        "item,comma",
        "item?question",
        "item~tilde",
        "item`backtick",
    ])
    def test_create_item_special_char_names(self, name):
        """Test create_item accepts special characters in names."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name


class TestCreateItemInvalidContentType:
    """Test create_item with invalid content types."""

    def test_create_item_malformed_json(self):
        """Test create_item rejects malformed JSON."""
        r = client.post("/items", content="{invalid json}", 
                       headers={"Content-Type": "application/json"})
        assert r.status_code == 422

    def test_create_item_wrong_content_type(self):
        """Test create_item with non-JSON content type."""
        r = client.post("/items", data="name=test&price=10",
                       headers={"Content-Type": "application/x-www-form-urlencoded"})
        assert r.status_code == 422
