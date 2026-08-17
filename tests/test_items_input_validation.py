"""
Input validation and boundary testing for FastAPI items endpoint.

Tests focus on price validation, name validation, missing fields,
type validation, and edge cases for create_item and get_item endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation in create_item endpoint."""

    @pytest.mark.parametrize("price", [
        -0.01,      # Small negative
        -1.0,       # Negative
        -100.0,     # Large negative
        0,          # Zero (boundary)
        0.0,        # Zero (float)
    ])
    def test_create_item_rejects_non_positive_price(self, price):
        """Test that non-positive prices are rejected with 400 status."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    @pytest.mark.parametrize("price", [
        0.01,           # Minimum valid
        0.1,            # Small positive
        1.0,            # Standard
        10.5,           # Decimal
        100.0,          # Large
        999999.99,      # Very large
    ])
    def test_create_item_accepts_positive_price(self, price):
        """Test that positive prices are accepted and returned correctly."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_create_item_price_high_precision(self):
        """Test price with high decimal precision."""
        r = client.post("/items", json={"name": "test", "price": 19.99})
        assert r.status_code == 200
        assert r.json()["price"] == 19.99

    def test_create_item_price_very_large(self):
        """Test very large price value."""
        r = client.post("/items", json={"name": "test", "price": 1e6})
        assert r.status_code == 200
        assert r.json()["price"] == 1e6


class TestCreateItemNameValidation:
    """Test name field validation in create_item endpoint."""

    @pytest.mark.parametrize("name", [
        "",                         # Empty string
        " ",                        # Whitespace only
        "  \t  ",                   # Whitespace and tabs
    ])
    def test_create_item_empty_name_accepted(self, name):
        """Test that empty/whitespace names are accepted by FastAPI."""
        # Note: FastAPI by default accepts empty strings for str fields.
        # This tests current behavior; validation could be added to API.
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200

    @pytest.mark.parametrize("name", [
        "book",                     # Simple
        "test item",                # With space
        "item-1",                   # With hyphen
        "item_2",                   # With underscore
        "item123",                  # With numbers
        "UPPERCASE",                # Uppercase
        "MixedCase",                # Mixed case
    ])
    def test_create_item_common_names(self, name):
        """Test that common name patterns are accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize("name", [
        "café",                     # Accented characters
        "日本語",                    # Japanese
        "Москва",                   # Cyrillic
        "العربية",                  # Arabic
        "emoji😀test",              # Emoji
    ])
    def test_create_item_unicode_names(self, name):
        """Test that unicode names are accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize("name", [
        "!@#$%^&*()",               # Special characters
        "test<>name",               # Angle brackets
        "test\"quote",              # Quote
        "test'apostrophe",          # Apostrophe
        "path/like",                # Forward slash
    ])
    def test_create_item_special_character_names(self, name):
        """Test that names with special characters are accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200

    def test_create_item_very_long_name(self):
        """Test that very long names are accepted."""
        long_name = "a" * 1000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_create_item_name_with_newlines(self):
        """Test name with newline characters."""
        r = client.post("/items", json={"name": "test\nname", "price": 10.0})
        assert r.status_code == 200

    def test_create_item_name_with_tabs(self):
        """Test name with tab characters."""
        r = client.post("/items", json={"name": "test\tname", "price": 10.0})
        assert r.status_code == 200


class TestCreateItemMissingFields:
    """Test handling of missing required fields."""

    def test_create_item_missing_name(self):
        """Test that missing name field returns validation error."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        assert "name" in r.text.lower()

    def test_create_item_missing_price(self):
        """Test that missing price field returns validation error."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        assert "price" in r.text.lower()

    def test_create_item_missing_all_fields(self):
        """Test that missing all fields returns validation error."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_create_item_empty_json(self):
        """Test that completely empty request returns error."""
        r = client.post("/items", json={})
        assert r.status_code == 422


class TestCreateItemTypeValidation:
    """Test type validation for request fields."""

    @pytest.mark.parametrize("price", [
        "10",                       # String number
        "10.5",                     # String decimal
        "zero",                     # Non-numeric string
        None,                       # None value
    ])
    def test_create_item_price_type_coercion(self, price):
        """Test price field type handling."""
        r = client.post("/items", json={"name": "test", "price": price})
        # Pydantic will try to coerce string numbers to float
        if isinstance(price, str) and price.replace(".", "").replace("-", "").isdigit():
            # Numeric strings get coerced
            if float(price) > 0:
                assert r.status_code == 200
            else:
                assert r.status_code == 400
        elif price is None:
            # None typically fails validation
            assert r.status_code == 422
        else:
            # Non-numeric strings fail validation
            assert r.status_code == 422

    @pytest.mark.parametrize("name_value", [
        123,                        # Integer instead of string
        12.5,                       # Float instead of string
        None,                       # None value
        [],                         # List
        {},                         # Dict
    ])
    def test_create_item_name_type_coercion(self, name_value):
        """Test name field type handling."""
        r = client.post("/items", json={"name": name_value, "price": 10.0})
        if isinstance(name_value, (int, float)):
            # Numbers get coerced to strings
            assert r.status_code == 200
        elif name_value is None or isinstance(name_value, (list, dict)):
            # None, lists, dicts fail validation
            assert r.status_code == 422


class TestCreateItemExtraFields:
    """Test handling of extra fields in request."""

    def test_create_item_with_extra_field(self):
        """Test that extra fields are ignored."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "extra_field": "ignored"
        })
        assert r.status_code == 200
        assert "extra_field" not in r.json()

    def test_create_item_with_multiple_extra_fields(self):
        """Test multiple extra fields are ignored."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "extra1": "value1",
            "extra2": "value2",
            "extra3": "value3"
        })
        assert r.status_code == 200
        response = r.json()
        assert "extra1" not in response
        assert "extra2" not in response
        assert "extra3" not in response

    def test_create_item_id_field_ignored(self):
        """Test that id field in request is ignored."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "id": 999
        })
        assert r.status_code == 200
        assert r.json()["id"] == 1  # Always returns id=1, not 999


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get_item endpoint."""

    @pytest.mark.parametrize("item_id", [
        0,                          # Zero
        -1,                         # Negative
        -100,                       # Large negative
    ])
    def test_get_item_not_found_boundary_ids(self, item_id):
        """Test that boundary item_ids return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]

    @pytest.mark.parametrize("item_id", [
        2,                          # Small non-matching ID
        10,                         # Medium ID
        999,                        # Large ID
        1000000,                    # Very large ID
    ])
    def test_get_item_not_found_various_ids(self, item_id):
        """Test that non-matching item_ids return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_get_item_found_id_1(self):
        """Test that item_id=1 returns 200."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    @pytest.mark.parametrize("param", [
        "abc",                      # Non-numeric string
        "1.5",                      # Float string
        "",                         # Empty
        " ",                        # Whitespace
    ])
    def test_get_item_invalid_path_parameter(self, param):
        """Test invalid path parameters."""
        r = client.get(f"/items/{param}")
        # FastAPI will return 422 for non-convertible path parameters
        assert r.status_code in [404, 422]


class TestItemResponseValidation:
    """Test response structure and types for item operations."""

    def test_create_item_response_structure(self):
        """Test create_item response contains required fields."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert len(data) == 3  # Only 3 fields

    def test_create_item_response_field_types(self):
        """Test create_item response field types."""
        r = client.post("/items", json={"name": "test", "price": 10.5})
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], float)

    def test_get_item_response_structure(self):
        """Test get_item response contains required fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_response_values(self):
        """Test get_item returns consistent values."""
        r = client.get("/items/1")
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0
