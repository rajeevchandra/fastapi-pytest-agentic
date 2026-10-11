"""Comprehensive input validation tests for /items POST endpoint."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemBasicSuccess:
    """Test basic successful item creation."""

    def test_create_item_with_valid_price(self):
        """Test creating an item with a valid positive price."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "book"
        assert data["price"] == 12.5

    def test_create_item_preserves_name(self):
        """Test that item name is preserved in response."""
        r = client.post("/items", json={"name": "laptop", "price": 999.99})
        assert r.status_code == 200
        assert r.json()["name"] == "laptop"

    def test_create_item_preserves_price(self):
        """Test that item price is preserved in response."""
        r = client.post("/items", json={"name": "pen", "price": 5.0})
        assert r.status_code == 200
        assert r.json()["price"] == 5.0


class TestCreateItemPriceBoundaries:
    """Test price boundary conditions."""

    @pytest.mark.parametrize("price", [0.01, 0.1, 1.0, 10.0, 100.0, 999.99, 9999.99])
    def test_create_item_various_positive_prices(self, price):
        """Test creating items with various valid positive prices."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_create_item_rejects_zero_price(self):
        """Test that price of 0 is rejected."""
        r = client.post("/items", json={"name": "invalid", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_rejects_negative_price(self):
        """Test that negative price is rejected."""
        r = client.post("/items", json={"name": "invalid", "price": -1})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_rejects_very_negative_price(self):
        """Test that very negative price is rejected."""
        r = client.post("/items", json={"name": "invalid", "price": -999.99})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [-100, -50, -1, -0.01])
    def test_create_item_rejects_all_negative_prices(self, price):
        """Test that all negative prices are rejected."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"


class TestCreateItemNameValidation:
    """Test name field validation."""

    def test_create_item_with_single_char_name(self):
        """Test creating item with single character name."""
        r = client.post("/items", json={"name": "a", "price": 1.0})
        assert r.status_code == 200
        assert r.json()["name"] == "a"

    def test_create_item_with_long_name(self):
        """Test creating item with a very long name."""
        long_name = "x" * 500
        r = client.post("/items", json={"name": long_name, "price": 1.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_create_item_with_special_characters_in_name(self):
        """Test creating item with special characters in name."""
        r = client.post("/items", json={"name": "item@#$%", "price": 1.0})
        assert r.status_code == 200
        assert r.json()["name"] == "item@#$%"

    def test_create_item_with_numbers_in_name(self):
        """Test creating item with numbers in name."""
        r = client.post("/items", json={"name": "item123", "price": 1.0})
        assert r.status_code == 200
        assert r.json()["name"] == "item123"

    def test_create_item_with_spaces_in_name(self):
        """Test creating item with spaces in name."""
        r = client.post("/items", json={"name": "my item", "price": 1.0})
        assert r.status_code == 200
        assert r.json()["name"] == "my item"

    def test_create_item_with_unicode_name(self):
        """Test creating item with unicode characters in name."""
        r = client.post("/items", json={"name": "日本語", "price": 1.0})
        assert r.status_code == 200
        assert r.json()["name"] == "日本語"

    def test_create_item_with_emoji_in_name(self):
        """Test creating item with emoji in name."""
        r = client.post("/items", json={"name": "book📚", "price": 1.0})
        assert r.status_code == 200
        assert r.json()["name"] == "book📚"


class TestCreateItemMissingFields:
    """Test missing required fields."""

    def test_create_item_missing_name_field(self):
        """Test that missing name field results in validation error."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_create_item_missing_price_field(self):
        """Test that missing price field results in validation error."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422

    def test_create_item_missing_all_fields(self):
        """Test that missing all fields results in validation error."""
        r = client.post("/items", json={})
        assert r.status_code == 422


class TestCreateItemInvalidDataTypes:
    """Test invalid data types for fields."""

    def test_create_item_price_as_string(self):
        """Test that string price is rejected (or auto-converted if Pydantic allows)."""
        # Pydantic will try to coerce string to float if possible
        r = client.post("/items", json={"name": "item", "price": "10.5"})
        # This may succeed (coercion) or fail (422) depending on Pydantic behavior
        # We test that it's handled consistently
        assert r.status_code in (200, 422)

    def test_create_item_price_as_null(self):
        """Test that null price is rejected."""
        r = client.post("/items", json={"name": "item", "price": None})
        assert r.status_code == 422

    def test_create_item_name_as_number(self):
        """Test that number as name is handled (Pydantic may coerce)."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # May succeed with coercion or fail with 422
        assert r.status_code in (200, 422)

    def test_create_item_name_as_null(self):
        """Test that null name is rejected."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422

    def test_create_item_with_list_payload(self):
        """Test that list payload is rejected."""
        r = client.post("/items", json=[{"name": "item", "price": 10.0}])
        assert r.status_code == 422

    def test_create_item_with_string_payload(self):
        """Test that string payload is rejected."""
        r = client.post("/items", json="invalid")
        assert r.status_code == 422


class TestCreateItemExtraFields:
    """Test behavior with extra fields."""

    def test_create_item_with_extra_field(self):
        """Test creating item with extra fields (should be ignored by Pydantic)."""
        r = client.post("/items", json={
            "name": "item",
            "price": 10.0,
            "extra": "field"
        })
        assert r.status_code == 200
        # Extra field should not be in response
        assert "extra" not in r.json()

    def test_create_item_with_multiple_extra_fields(self):
        """Test creating item with multiple extra fields."""
        r = client.post("/items", json={
            "name": "item",
            "price": 10.0,
            "extra1": "value1",
            "extra2": "value2"
        })
        assert r.status_code == 200
        data = r.json()
        assert "extra1" not in data
        assert "extra2" not in data


class TestCreateItemResponseStructure:
    """Test response structure and fields."""

    def test_create_item_response_has_id(self):
        """Test that response includes id field."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert "id" in r.json()

    def test_create_item_response_has_name(self):
        """Test that response includes name field."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert "name" in r.json()

    def test_create_item_response_has_price(self):
        """Test that response includes price field."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert "price" in r.json()

    def test_create_item_response_has_only_expected_fields(self):
        """Test that response has only expected fields."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert set(data.keys()) == {"id", "name", "price"}
