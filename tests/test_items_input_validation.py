"""
Input validation and boundary testing for /items POST endpoint.

Tests cover:
- Price boundary conditions (negative, zero, large values)
- Name field variations (empty, special chars, long strings)
- Missing required fields
- Response structure validation
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation for creating items."""

    @pytest.mark.parametrize(
        "price",
        [
            -1.0,
            -100.0,
            -0.01,
        ],
    )
    def test_create_item_rejects_negative_price(self, price):
        """Negative prices should be rejected."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize(
        "price",
        [
            0.0,
            0,
        ],
    )
    def test_create_item_rejects_zero_price(self, price):
        """Zero price should be rejected."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize(
        "price",
        [
            0.01,
            1.0,
            10.5,
            99.99,
            999999.99,
            1000000.0,
        ],
    )
    def test_create_item_accepts_positive_price(self, price):
        """Positive prices should be accepted."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize(
        "price",
        [
            1e-6,
            1e-10,
        ],
    )
    def test_create_item_accepts_very_small_positive_price(self, price):
        """Very small positive prices should be accepted."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] > 0


class TestCreateItemNameValidation:
    """Test name field validation for creating items."""

    def test_create_item_accepts_normal_name(self):
        """Normal names should be accepted."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "book"

    @pytest.mark.parametrize(
        "name",
        [
            "A",
            "a",
            "1",
            "Item Name",
            "item-name",
            "item_name",
            "item.name",
        ],
    )
    def test_create_item_accepts_various_names(self, name):
        """Various name formats should be accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_accepts_empty_name(self):
        """Empty names are technically valid at API level (Pydantic doesn't reject)."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == ""

    def test_create_item_accepts_very_long_name(self):
        """Very long names should be accepted."""
        long_name = "a" * 500
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    @pytest.mark.parametrize(
        "name",
        [
            "!@#$%",
            "name@domain",
            "name/with/slash",
            "name\\with\\backslash",
            "name\nwith\nnewline",
            "name\twith\ttab",
            "😀emoji",
            "日本語",
        ],
    )
    def test_create_item_accepts_special_chars_in_name(self, name):
        """Special characters and unicode should be accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestCreateItemMissingFields:
    """Test handling of missing required fields."""

    def test_create_item_missing_name(self):
        """Missing name should return 422 validation error."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_create_item_missing_price(self):
        """Missing price should return 422 validation error."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422

    def test_create_item_missing_both_fields(self):
        """Missing both fields should return 422 validation error."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_create_item_with_extra_field(self):
        """Extra fields should be ignored by Pydantic."""
        r = client.post("/items", json={"name": "item", "price": 10.0, "extra": "field"})
        assert r.status_code == 200
        assert r.json()["name"] == "item"
        assert r.json()["price"] == 10.0
        assert "extra" not in r.json()


class TestCreateItemInvalidTypes:
    """Test type validation for request fields."""

    def test_create_item_price_as_string(self):
        """Price as string should fail type validation."""
        r = client.post("/items", json={"name": "item", "price": "10.0"})
        assert r.status_code == 422

    def test_create_item_price_as_null(self):
        """Price as null should fail validation."""
        r = client.post("/items", json={"name": "item", "price": None})
        assert r.status_code == 422

    def test_create_item_name_as_number(self):
        """Name can be provided as number and will be coerced to string."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # Pydantic coerces numbers to strings for str fields
        assert r.status_code == 200
        assert r.json()["name"] == "123"

    def test_create_item_name_as_null(self):
        """Name as null should fail validation."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422


class TestCreateItemResponseStructure:
    """Test response structure validation."""

    def test_create_item_response_has_required_fields(self):
        """Response should contain id, name, and price fields."""
        r = client.post("/items", json={"name": "test", "price": 5.0})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_field_types(self):
        """Response fields should have correct types."""
        r = client.post("/items", json={"name": "test", "price": 5.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_create_item_response_id_is_one(self):
        """Response id should always be 1 (hardcoded)."""
        r1 = client.post("/items", json={"name": "item1", "price": 5.0})
        r2 = client.post("/items", json={"name": "item2", "price": 10.0})
        assert r1.json()["id"] == 1
        assert r2.json()["id"] == 1

    def test_create_item_response_preserves_input(self):
        """Response name and price should match input."""
        name = "book"
        price = 15.5
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price


class TestCreateItemErrorHandling:
    """Test error response consistency."""

    def test_error_response_has_detail_field(self):
        """Error responses should have a detail field."""
        r = client.post("/items", json={"name": "item", "price": -1})
        assert r.status_code == 400
        assert "detail" in r.json()

    def test_error_detail_is_string(self):
        """Error detail should be a string."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        assert isinstance(r.json()["detail"], str)

    def test_validation_error_response_structure(self):
        """Validation errors should follow FastAPI error format."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data
        # FastAPI validation errors include a detail array
        assert isinstance(data["detail"], (list, str, dict))

    @pytest.mark.parametrize(
        "payload",
        [
            '{"name": "item", "price": 10.0}',
            '{"name": "item"}',
            '',
        ],
    )
    def test_create_item_handles_various_payloads(self, payload):
        """API should handle various JSON payloads gracefully."""
        r = client.post("/items", content=payload, headers={"content-type": "application/json"})
        # Should either succeed or return 4xx, not 5xx
        assert r.status_code < 500
