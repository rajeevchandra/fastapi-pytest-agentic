"""Test input validation for item creation endpoint."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation for create_item endpoint."""

    @pytest.mark.parametrize("price", [
        -100,
        -1,
        -0.01,
        0,
    ])
    def test_create_item_rejects_non_positive_price(self, price):
        """Test that non-positive prices are rejected."""
        response = client.post("/items", json={"name": "book", "price": price})
        assert response.status_code == 400
        assert response.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [
        0.01,
        1,
        100,
        1000.50,
        1e10,
    ])
    def test_create_item_accepts_positive_price(self, price):
        """Test that positive prices are accepted."""
        response = client.post("/items", json={"name": "book", "price": price})
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == price

    def test_create_item_price_boundary_just_above_zero(self):
        """Test smallest valid price (0.01)."""
        response = client.post("/items", json={"name": "item", "price": 0.01})
        assert response.status_code == 200
        assert response.json()["price"] == 0.01

    def test_create_item_price_very_large(self):
        """Test very large price values."""
        large_price = 1e15
        response = client.post("/items", json={"name": "luxury", "price": large_price})
        assert response.status_code == 200
        assert response.json()["price"] == large_price


class TestCreateItemNameValidation:
    """Test name field validation for create_item endpoint."""

    @pytest.mark.parametrize("name", [
        "book",
        "laptop",
        "A",
        "Product 123",
        "item_name",
    ])
    def test_create_item_accepts_valid_names(self, name):
        """Test that valid names are accepted."""
        response = client.post("/items", json={"name": name, "price": 10.5})
        assert response.status_code == 200
        assert response.json()["name"] == name

    def test_create_item_name_single_char(self):
        """Test single character name."""
        response = client.post("/items", json={"name": "X", "price": 5})
        assert response.status_code == 200
        assert response.json()["name"] == "X"

    def test_create_item_name_with_spaces(self):
        """Test name with spaces."""
        response = client.post("/items", json={"name": "blue book", "price": 15})
        assert response.status_code == 200
        assert response.json()["name"] == "blue book"

    def test_create_item_name_with_special_chars(self):
        """Test name with special characters."""
        response = client.post("/items", json={"name": "item-#123", "price": 20})
        assert response.status_code == 200
        assert response.json()["name"] == "item-#123"

    def test_create_item_name_long_string(self):
        """Test very long name string."""
        long_name = "a" * 500
        response = client.post("/items", json={"name": long_name, "price": 30})
        assert response.status_code == 200
        assert response.json()["name"] == long_name

    def test_create_item_name_unicode(self):
        """Test Unicode characters in name."""
        response = client.post("/items", json={"name": "café ☕", "price": 8.5})
        assert response.status_code == 200
        assert response.json()["name"] == "café ☕"

    def test_create_item_name_empty_string(self):
        """Test empty name string - should be accepted by FastAPI/Pydantic."""
        response = client.post("/items", json={"name": "", "price": 5})
        # Pydantic BaseModel accepts empty strings unless explicitly restricted
        assert response.status_code == 200
        assert response.json()["name"] == ""


class TestCreateItemMissingFields:
    """Test missing required fields."""

    def test_create_item_missing_name(self):
        """Test missing name field."""
        response = client.post("/items", json={"price": 10})
        assert response.status_code == 422  # Unprocessable Entity

    def test_create_item_missing_price(self):
        """Test missing price field."""
        response = client.post("/items", json={"name": "item"})
        assert response.status_code == 422  # Unprocessable Entity

    def test_create_item_missing_all_fields(self):
        """Test missing all fields."""
        response = client.post("/items", json={})
        assert response.status_code == 422  # Unprocessable Entity

    def test_create_item_empty_json(self):
        """Test with empty JSON body."""
        response = client.post("/items", json={})
        assert response.status_code == 422


class TestCreateItemInvalidTypes:
    """Test invalid field types."""

    def test_create_item_price_as_string(self):
        """Test price as string."""
        response = client.post("/items", json={"name": "item", "price": "10.5"})
        # Pydantic coerces strings to floats if valid
        assert response.status_code == 200

    def test_create_item_price_as_null(self):
        """Test price as null."""
        response = client.post("/items", json={"name": "item", "price": None})
        assert response.status_code == 422

    def test_create_item_name_as_number(self):
        """Test name as number."""
        response = client.post("/items", json={"name": 123, "price": 10})
        # Pydantic coerces numbers to strings
        assert response.status_code == 200
        assert response.json()["name"] == "123"

    def test_create_item_name_as_null(self):
        """Test name as null."""
        response = client.post("/items", json={"name": None, "price": 10})
        assert response.status_code == 422

    def test_create_item_extra_fields(self):
        """Test with extra unknown fields."""
        response = client.post("/items", json={
            "name": "item",
            "price": 10,
            "extra_field": "extra_value",
            "another_field": 123,
        })
        # FastAPI/Pydantic ignores extra fields by default
        assert response.status_code == 200
        assert response.json()["name"] == "item"
        assert response.json()["price"] == 10


class TestCreateItemResponseStructure:
    """Test response structure for successful creation."""

    def test_create_item_response_has_required_fields(self):
        """Test that response contains all expected fields."""
        response = client.post("/items", json={"name": "book", "price": 15.99})
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_field_types(self):
        """Test that response fields have correct types."""
        response = client.post("/items", json={"name": "pen", "price": 2.50})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_create_item_id_always_one(self):
        """Test that created item always has id=1."""
        response = client.post("/items", json={"name": "item1", "price": 5})
        assert response.status_code == 200
        assert response.json()["id"] == 1


class TestCreateItemEdgeCases:
    """Test edge cases and special scenarios."""

    def test_create_item_float_precision(self):
        """Test price with high decimal precision."""
        response = client.post("/items", json={"name": "item", "price": 10.123456789})
        assert response.status_code == 200
        # Float may be rounded due to precision limits
        assert response.json()["price"] == pytest.approx(10.123456789, rel=1e-6)

    def test_create_item_negative_zero(self):
        """Test negative zero price."""
        response = client.post("/items", json={"name": "item", "price": -0.0})
        # -0.0 == 0 in Python
        assert response.status_code == 400

    def test_create_item_scientific_notation(self):
        """Test price in scientific notation."""
        response = client.post("/items", json={"name": "item", "price": 1.5e3})
        assert response.status_code == 200
        assert response.json()["price"] == 1500.0

    def test_create_item_newline_in_name(self):
        """Test name with newline characters."""
        response = client.post("/items", json={"name": "item\nname", "price": 10})
        assert response.status_code == 200
        assert response.json()["name"] == "item\nname"

    def test_create_item_tab_in_name(self):
        """Test name with tab characters."""
        response = client.post("/items", json={"name": "item\tname", "price": 10})
        assert response.status_code == 200
        assert response.json()["name"] == "item\tname"
