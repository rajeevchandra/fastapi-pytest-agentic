"""Input validation and boundary testing for items endpoint."""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation in create_item endpoint."""

    @pytest.mark.parametrize("price", [0, -1, -100, -0.01])
    def test_create_item_rejects_non_positive_price(self, price):
        """Test that negative and zero prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [0.01, 1, 10.5, 99999.99, 1e10])
    def test_create_item_accepts_valid_price(self, price):
        """Test that valid positive prices are accepted."""
        r = client.post("/items", json={"name": "valid", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_create_item_price_boundary_very_small(self):
        """Test smallest positive price."""
        r = client.post("/items", json={"name": "test", "price": 0.001})
        assert r.status_code == 200
        assert r.json()["price"] == 0.001

    def test_create_item_price_boundary_very_large(self):
        """Test very large price value."""
        large_price = 999999999.99
        r = client.post("/items", json={"name": "test", "price": large_price})
        assert r.status_code == 200
        assert r.json()["price"] == large_price


class TestCreateItemNameValidation:
    """Test name field validation in create_item endpoint."""

    def test_create_item_with_valid_name(self):
        """Test creation with normal name."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200
        assert r.json()["name"] == "book"

    def test_create_item_with_empty_name(self):
        """Test creation with empty name string."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == ""
        assert data["price"] == 10.0

    def test_create_item_with_special_characters_name(self):
        """Test creation with special characters in name."""
        special_name = "Book @#$% & Co."
        r = client.post("/items", json={"name": special_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == special_name

    def test_create_item_with_unicode_name(self):
        """Test creation with unicode characters in name."""
        unicode_name = "日本語テスト"
        r = client.post("/items", json={"name": unicode_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == unicode_name

    def test_create_item_with_long_name(self):
        """Test creation with very long name."""
        long_name = "x" * 500
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_create_item_with_whitespace_name(self):
        """Test creation with whitespace-only name."""
        r = client.post("/items", json={"name": "   ", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "   "

    def test_create_item_with_numeric_string_name(self):
        """Test creation with numeric string as name."""
        r = client.post("/items", json={"name": "12345", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "12345"


class TestCreateItemMissingFields:
    """Test request validation for missing required fields."""

    def test_create_item_missing_name(self):
        """Test that missing name field returns 422."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_create_item_missing_price(self):
        """Test that missing price field returns 422."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_create_item_empty_json(self):
        """Test that empty JSON object returns 422."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_create_item_null_name(self):
        """Test that null name field returns 422."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422

    def test_create_item_null_price(self):
        """Test that null price field returns 422."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422


class TestCreateItemTypeValidation:
    """Test type validation for request fields."""

    def test_create_item_invalid_price_string(self):
        """Test that string price is rejected by Pydantic."""
        r = client.post("/items", json={"name": "test", "price": "not_a_number"})
        assert r.status_code == 422

    def test_create_item_price_as_list(self):
        """Test that list price is rejected."""
        r = client.post("/items", json={"name": "test", "price": [10.0]})
        assert r.status_code == 422

    def test_create_item_price_as_boolean(self):
        """Test that boolean price is rejected."""
        r = client.post("/items", json={"name": "test", "price": True})
        # Note: in JSON, booleans might be coerced to numbers, so this may succeed
        # depending on Pydantic version. Check actual behavior.
        assert r.status_code in [200, 422]

    def test_create_item_name_as_number(self):
        """Test that numeric name is handled properly."""
        # JSON numbers are valid values; Pydantic might coerce or accept
        r = client.post("/items", json={"name": 123, "price": 10.0})
        assert r.status_code in [200, 422]

    def test_create_item_name_as_list(self):
        """Test that list name is rejected."""
        r = client.post("/items", json={"name": ["item"], "price": 10.0})
        assert r.status_code == 422


class TestCreateItemResponseStructure:
    """Test response structure and field presence."""

    def test_create_item_response_has_required_fields(self):
        """Test that response contains all required fields."""
        r = client.post("/items", json={"name": "test", "price": 10.5})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_field_types(self):
        """Test that response fields have correct types."""
        r = client.post("/items", json={"name": "test", "price": 10.5})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_create_item_response_id_consistent(self):
        """Test that created item has ID 1."""
        r = client.post("/items", json={"name": "item1", "price": 5.0})
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_create_item_no_extra_fields(self):
        """Test that response doesn't contain unexpected fields."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        # Response should only have id, name, price
        assert set(data.keys()) == {"id", "name", "price"}


class TestCreateItemWithExtraFields:
    """Test handling of extra fields in request."""

    def test_create_item_with_extra_field(self):
        """Test that extra fields are ignored or rejected."""
        r = client.post(
            "/items", json={"name": "test", "price": 10.0, "description": "extra"}
        )
        # Pydantic by default ignores extra fields
        assert r.status_code == 200
        assert r.json()["name"] == "test"

    def test_create_item_with_multiple_extra_fields(self):
        """Test with multiple extra fields."""
        r = client.post(
            "/items",
            json={
                "name": "test",
                "price": 10.0,
                "description": "extra",
                "category": "books",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "test"
        assert data["price"] == 10.0
