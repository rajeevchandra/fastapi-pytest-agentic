import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation in create_item endpoint."""

    @pytest.mark.parametrize("price", [-100, -1, -0.01, 0])
    def test_create_item_rejects_non_positive_prices(self, price):
        """Price must be > 0."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    @pytest.mark.parametrize("price", [0.01, 1, 10.5, 100, 1e10])
    def test_create_item_accepts_positive_prices(self, price):
        """Positive prices should be accepted."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_create_item_price_type_coercion_from_string(self):
        """Pydantic should coerce string to float for price."""
        r = client.post("/items", json={"name": "item", "price": "10.5"})
        assert r.status_code == 200
        assert r.json()["price"] == 10.5

    def test_create_item_price_type_coercion_from_int(self):
        """Pydantic should coerce int to float for price."""
        r = client.post("/items", json={"name": "item", "price": 10})
        assert r.status_code == 200
        assert r.json()["price"] == 10.0


class TestCreateItemNameValidation:
    """Test name field validation in create_item endpoint."""

    def test_create_item_with_simple_name(self):
        """Simple ASCII names should be accepted."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "book"

    def test_create_item_with_empty_name(self):
        """Empty string name should be accepted (no validation for empty)."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == ""

    def test_create_item_with_unicode_name(self):
        """Unicode characters should be accepted in name."""
        r = client.post("/items", json={"name": "本书", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "本书"

    def test_create_item_with_special_characters_in_name(self):
        """Special characters should be accepted."""
        name = "book!@#$%^&*()"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_with_long_name(self):
        """Very long names should be accepted."""
        long_name = "a" * 1000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_create_item_with_whitespace_name(self):
        """Names with only whitespace should be accepted."""
        r = client.post("/items", json={"name": "   ", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "   "


class TestCreateItemMissingFields:
    """Test missing required fields in create_item endpoint."""

    def test_create_item_missing_price(self):
        """Missing price field should return validation error."""
        r = client.post("/items", json={"name": "book"})
        assert r.status_code == 422

    def test_create_item_missing_name(self):
        """Missing name field should return validation error."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_create_item_missing_both_fields(self):
        """Missing both required fields should return validation error."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_create_item_with_null_price(self):
        """Null price should return validation error."""
        r = client.post("/items", json={"name": "book", "price": None})
        assert r.status_code == 422

    def test_create_item_with_null_name(self):
        """Null name should return validation error."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422


class TestCreateItemInvalidTypes:
    """Test invalid field types in create_item endpoint."""

    def test_create_item_price_is_object(self):
        """Price as object should return validation error."""
        r = client.post("/items", json={"name": "item", "price": {}})
        assert r.status_code == 422

    def test_create_item_price_is_array(self):
        """Price as array should return validation error."""
        r = client.post("/items", json={"name": "item", "price": [1, 2, 3]})
        assert r.status_code == 422

    def test_create_item_price_is_invalid_string(self):
        """Price as non-numeric string should return validation error."""
        r = client.post("/items", json={"name": "item", "price": "invalid"})
        assert r.status_code == 422

    def test_create_item_name_is_numeric(self):
        """Name as number should be coerced to string (JSON behavior)."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        assert r.status_code == 200

    def test_create_item_name_is_array(self):
        """Name as array should return validation error."""
        r = client.post("/items", json={"name": ["book"], "price": 10.0})
        assert r.status_code == 422


class TestCreateItemBoundaryConditions:
    """Test boundary conditions and edge cases."""

    def test_create_item_price_very_small_positive(self):
        """Very small positive price should be accepted."""
        r = client.post("/items", json={"name": "item", "price": 1e-10})
        assert r.status_code == 200
        assert r.json()["price"] > 0

    def test_create_item_price_very_large(self):
        """Very large prices should be accepted."""
        r = client.post("/items", json={"name": "item", "price": 1e15})
        assert r.status_code == 200
        assert r.json()["price"] == 1e15

    def test_create_item_with_extra_fields(self):
        """Extra fields should be ignored (Pydantic default)."""
        r = client.post(
            "/items", 
            json={"name": "item", "price": 10.0, "extra": "field", "another": 123}
        )
        assert r.status_code == 200
        assert r.json()["name"] == "item"

    def test_create_item_response_contains_required_fields(self):
        """Response should contain all required fields."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
