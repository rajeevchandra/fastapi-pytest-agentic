"""Test input validation and boundary conditions for /items endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation for POST /items."""

    @pytest.mark.parametrize("price", [-100, -1, -0.01, 0])
    def test_create_item_rejects_non_positive_price(self, price):
        """Price must be > 0; negative and zero prices should raise 400."""
        response = client.post("/items", json={"name": "item", "price": price})
        assert response.status_code == 400
        assert response.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [0.01, 1, 100.5, 999999.99, 1e10])
    def test_create_item_accepts_positive_price(self, price):
        """All positive prices should be accepted."""
        response = client.post("/items", json={"name": "item", "price": price})
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == price

    def test_create_item_price_as_string_coerced(self):
        """Pydantic coerces string prices to float."""
        response = client.post("/items", json={"name": "item", "price": "10.5"})
        assert response.status_code == 200
        assert response.json()["price"] == 10.5


class TestCreateItemNameValidation:
    """Test name field validation for POST /items."""

    @pytest.mark.parametrize("name", ["", " ", "  "])
    def test_create_item_accepts_whitespace_name(self, name):
        """Empty and whitespace strings should be accepted (Pydantic validates as str)."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == name

    def test_create_item_long_name(self):
        """Very long name strings should be accepted."""
        long_name = "a" * 1000
        response = client.post("/items", json={"name": long_name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == long_name

    @pytest.mark.parametrize(
        "name", ["book", "用户", "Café", "item-123", "item@store", "Test_Item"]
    )
    def test_create_item_special_char_names(self, name):
        """Special characters and unicode should be accepted."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == name


class TestCreateItemMissingFields:
    """Test missing required fields for POST /items."""

    def test_create_item_missing_price(self):
        """Missing price field should raise 422 validation error."""
        response = client.post("/items", json={"name": "item"})
        assert response.status_code == 422

    def test_create_item_missing_name(self):
        """Missing name field should raise 422 validation error."""
        response = client.post("/items", json={"price": 10.0})
        assert response.status_code == 422

    def test_create_item_empty_payload(self):
        """Empty JSON object should raise 422 validation error."""
        response = client.post("/items", json={})
        assert response.status_code == 422


class TestCreateItemTypeValidation:
    """Test type validation for POST /items fields."""

    def test_create_item_price_null_fails(self):
        """Null price should raise 422 validation error."""
        response = client.post("/items", json={"name": "item", "price": None})
        assert response.status_code == 422

    def test_create_item_name_null_fails(self):
        """Null name should raise 422 validation error."""
        response = client.post("/items", json={"name": None, "price": 10.0})
        assert response.status_code == 422

    def test_create_item_name_number_type(self):
        """Numbers for name field may be coerced to string by Pydantic."""
        response = client.post("/items", json={"name": 123, "price": 10.0})
        # Pydantic coerces numbers to strings
        assert response.status_code == 200
        assert response.json()["name"] == "123"

    def test_create_item_price_list_fails(self):
        """List for price should raise 422 validation error."""
        response = client.post("/items", json={"name": "item", "price": [10.0]})
        assert response.status_code == 422


class TestCreateItemExtraFields:
    """Test handling of extra fields in POST /items."""

    def test_create_item_with_extra_field(self):
        """Extra fields should be ignored by Pydantic."""
        response = client.post(
            "/items",
            json={"name": "item", "price": 10.0, "description": "extra field"},
        )
        assert response.status_code == 200
        # Extra field should not appear in response
        data = response.json()
        assert "description" not in data
        assert data["name"] == "item"
        assert data["price"] == 10.0


class TestCreateItemResponseStructure:
    """Test response structure and field types for POST /items."""

    def test_create_item_response_has_required_fields(self):
        """Response should include id, name, and price fields."""
        response = client.post("/items", json={"name": "book", "price": 12.5})
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_field_types(self):
        """Response fields should have correct types."""
        response = client.post("/items", json={"name": "book", "price": 12.5})
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    @pytest.mark.parametrize("price", [0.01, 1, 100, 999999.99])
    def test_create_item_returns_input_data(self, price):
        """Response should echo back the input name and price."""
        name = "test_item"
        response = client.post("/items", json={"name": name, "price": price})
        data = response.json()
        assert data["name"] == name
        assert data["price"] == price
