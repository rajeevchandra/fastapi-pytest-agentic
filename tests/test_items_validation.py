"""
Comprehensive input validation tests for /items POST endpoint.
Tests edge cases, boundary conditions, and error scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation for create_item endpoint."""

    def test_create_item_zero_price_rejected(self):
        """Verify zero price is rejected with 400 status."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [-1, -0.01, -100, -999.99])
    def test_create_item_negative_price_rejected(self, price):
        """Verify negative prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [0.01, 1, 10.5, 100, 999.99, 1000000])
    def test_create_item_valid_positive_prices(self, price):
        """Verify various positive prices are accepted."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price


class TestCreateItemInputValidation:
    """Test required field and data type validation."""

    def test_create_item_missing_name(self):
        """Verify missing name field returns 422 validation error."""
        r = client.post("/items", json={"price": 10})
        assert r.status_code == 422

    def test_create_item_missing_price(self):
        """Verify missing price field returns 422 validation error."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_create_item_empty_payload(self):
        """Verify empty JSON object returns 422 validation error."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_create_item_price_as_string(self):
        """Verify string price value returns 422 validation error."""
        r = client.post("/items", json={"name": "test", "price": "10"})
        assert r.status_code == 422

    def test_create_item_price_as_null(self):
        """Verify null price returns 422 validation error."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422

    def test_create_item_name_as_number(self):
        """Verify numeric name value returns 422 validation error."""
        r = client.post("/items", json={"name": 123, "price": 10})
        assert r.status_code == 422

    def test_create_item_name_as_null(self):
        """Verify null name returns 422 validation error."""
        r = client.post("/items", json={"name": None, "price": 10})
        assert r.status_code == 422


class TestCreateItemNameValidation:
    """Test name field edge cases and boundary conditions."""

    def test_create_item_empty_name(self):
        """Verify empty string name is technically valid from Pydantic perspective."""
        r = client.post("/items", json={"name": "", "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == ""

    def test_create_item_whitespace_name(self):
        """Verify whitespace-only name is accepted."""
        r = client.post("/items", json={"name": "   ", "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == "   "

    @pytest.mark.parametrize("name", [
        "a",
        "A",
        "test-item",
        "test_item",
        "test item",
        "Test Item 123",
        "café",
        "日本語",
        "emoji 🎉",
    ])
    def test_create_item_various_valid_names(self, name):
        """Verify various valid name strings are accepted."""
        r = client.post("/items", json={"name": name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_very_long_name(self):
        """Verify very long name strings are accepted."""
        long_name = "a" * 1000
        r = client.post("/items", json={"name": long_name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == long_name


class TestCreateItemExtraFields:
    """Test handling of extra fields in request."""

    def test_create_item_with_extra_field(self):
        """Verify extra fields in JSON are ignored by Pydantic."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10,
            "extra_field": "should be ignored"
        })
        assert r.status_code == 200
        assert r.json()["name"] == "test"
        assert r.json()["price"] == 10

    def test_create_item_with_multiple_extra_fields(self):
        """Verify multiple extra fields are safely ignored."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10,
            "id": 999,
            "description": "should be ignored",
            "tags": ["ignored"]
        })
        assert r.status_code == 200
        assert r.json()["price"] == 10


class TestCreateItemResponseStructure:
    """Test response structure and data types."""

    def test_create_item_response_has_required_fields(self):
        """Verify response contains all required fields."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_id_is_integer(self):
        """Verify id field is an integer."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        assert isinstance(r.json()["id"], int)

    def test_create_item_response_price_is_number(self):
        """Verify price field preserves numeric type."""
        r = client.post("/items", json={"name": "test", "price": 10.5})
        assert r.status_code == 200
        assert isinstance(r.json()["price"], (int, float))


class TestCreateItemContentType:
    """Test content type and malformed request handling."""

    def test_create_item_with_invalid_json(self):
        """Verify invalid JSON returns 422."""
        r = client.post("/items", content="{invalid json}", headers={"content-type": "application/json"})
        assert r.status_code == 422

    def test_create_item_no_content_type(self):
        """Verify request without proper content-type returns error."""
        r = client.post("/items", data='{"name": "test", "price": 10}')
        assert r.status_code in [400, 422]
