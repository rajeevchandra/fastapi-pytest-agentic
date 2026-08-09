"""Input validation and boundary testing for items endpoint."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price validation in create_item endpoint."""

    @pytest.mark.parametrize("price", [
        -100.5,      # negative price
        -1,          # negative single
        -0.01,       # small negative
        0,           # zero
        0.0,         # zero float
    ])
    def test_reject_non_positive_prices(self, price):
        """Test that non-positive prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [
        0.01,        # smallest positive
        0.001,       # very small
        1,           # integer
        1.5,         # decimal
        100,         # large
        999999.99,   # very large
    ])
    def test_accept_positive_prices(self, price):
        """Test that positive prices are accepted."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price


class TestCreateItemNameValidation:
    """Test name validation in create_item endpoint."""

    @pytest.mark.parametrize("name", [
        "",                           # empty
        "a",                          # single char
        "A",                          # single uppercase
        "123",                        # numbers only
        "test item",                  # with space
        "test-item",                  # with hyphen
        "test_item",                  # with underscore
        "test@item",                  # with special char
        "x" * 100,                    # very long
        "café",                       # unicode
        "日本語",                       # non-Latin chars
        "item!@#$%",                  # multiple special chars
    ])
    def test_accept_name_variations(self, name):
        """Test various name formats are accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestCreateItemMissingFields:
    """Test missing field handling in create_item."""

    def test_missing_name_field(self):
        """Test that missing name field returns validation error."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422  # validation error

    def test_missing_price_field(self):
        """Test that missing price field returns validation error."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422  # validation error

    def test_empty_request_body(self):
        """Test that empty request body returns validation error."""
        r = client.post("/items", json={})
        assert r.status_code == 422  # validation error


class TestCreateItemInvalidTypes:
    """Test type validation in create_item."""

    def test_price_as_string(self):
        """Test that string price fails validation."""
        r = client.post("/items", json={"name": "test", "price": "10.0"})
        assert r.status_code == 422

    def test_name_as_number(self):
        """Test that numeric name is coerced to string."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "123"

    def test_price_as_boolean(self):
        """Test that boolean price fails validation."""
        r = client.post("/items", json={"name": "test", "price": True})
        assert r.status_code == 422

    def test_extra_fields_ignored(self):
        """Test that extra fields are ignored."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "extra": "field",
            "another": "value"
        })
        assert r.status_code == 200
        assert "extra" not in r.json()


class TestCreateItemResponseStructure:
    """Test response structure of create_item."""

    def test_response_contains_id_name_price(self):
        """Test response contains all expected fields."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert len(data) == 3

    def test_id_is_always_one(self):
        """Test that returned id is always 1."""
        for i in range(3):
            r = client.post("/items", json={"name": f"test{i}", "price": 10.0 + i})
            assert r.json()["id"] == 1

    def test_response_fields_match_input(self):
        """Test response fields match input (except id)."""
        test_name = "widget"
        test_price = 25.50
        r = client.post("/items", json={"name": test_name, "price": test_price})
        data = r.json()
        assert data["name"] == test_name
        assert data["price"] == test_price
