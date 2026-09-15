"""Comprehensive input validation tests for POST /items endpoint."""
from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation in create_item."""

    @pytest.mark.parametrize("price", [-100, -1, -0.01, 0])
    def test_reject_non_positive_price(self, price):
        """Price must be strictly positive (> 0)."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    @pytest.mark.parametrize("price", [0.01, 1, 10.5, 100, 1e10])
    def test_accept_positive_price(self, price):
        """Accept various positive price values."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_price_string_coercion(self):
        """Pydantic auto-coerces valid string prices to float."""
        r = client.post("/items", json={"name": "test", "price": "10.5"})
        assert r.status_code == 200
        assert r.json()["price"] == 10.5


class TestCreateItemNameValidation:
    """Test name field validation in create_item."""

    def test_accept_normal_name(self):
        """Accept normal string names."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "book"

    def test_accept_long_name(self):
        """Accept very long names."""
        long_name = "a" * 1000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_accept_special_chars_in_name(self):
        """Accept special characters in name."""
        names = ["item-1", "test_name", "product.v2", "café", "日本語"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name

    def test_accept_empty_name(self):
        """Accept empty string as name (no validation)."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == ""

    def test_accept_whitespace_name(self):
        """Accept whitespace-only names."""
        r = client.post("/items", json={"name": "   ", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "   "


class TestCreateItemMissingFields:
    """Test validation when required fields are missing."""

    def test_missing_name_field(self):
        """Missing name field causes validation error."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_missing_price_field(self):
        """Missing price field causes validation error."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_missing_both_fields(self):
        """Missing both fields causes validation error."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_empty_json_body(self):
        """Empty request body causes validation error."""
        r = client.post("/items", json=None)
        assert r.status_code != 200  # Should fail validation

    def test_null_name(self):
        """Null name should fail validation."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422

    def test_null_price(self):
        """Null price should fail validation."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422


class TestCreateItemExtraFields:
    """Test handling of extra fields in request."""

    def test_extra_fields_ignored(self):
        """Extra fields are ignored by Pydantic."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "extra_field": "should be ignored",
            "another": 123
        })
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "test"
        assert data["price"] == 10.0


class TestCreateItemResponseFormat:
    """Test response format structure."""

    def test_response_contains_id(self):
        """Response includes id field."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert "id" in r.json()

    def test_response_id_value(self):
        """Response id is always 1."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_response_reflects_input(self):
        """Response name and price match input."""
        input_data = {"name": "widget", "price": 25.99}
        r = client.post("/items", json=input_data)
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == input_data["name"]
        assert data["price"] == input_data["price"]

    def test_response_has_all_required_fields(self):
        """Response includes id, name, and price."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert set(data.keys()) == {"id", "name", "price"}
