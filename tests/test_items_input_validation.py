"""
Input validation tests for item creation endpoint.
Covers boundary conditions, edge cases, and required field validation.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price validation for create_item endpoint."""

    @pytest.mark.parametrize("price,expected_status", [
        (-100, 400),
        (-1, 400),
        (-0.01, 400),
        (0, 400),
        (0.01, 200),
        (1, 200),
        (100, 200),
        (1000000, 200),
        (1e10, 200),
    ])
    def test_create_item_price_boundaries(self, price, expected_status):
        """Test price boundaries including negative, zero, and large values."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == expected_status

    @pytest.mark.parametrize("price", [0.01, 1, 10.5, 999.99])
    def test_create_item_valid_prices_return_correct_data(self, price):
        """Test that valid prices return correct item data."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price
        assert "id" in data
        assert "name" in data

    def test_create_item_price_zero_returns_error_detail(self):
        """Test that price=0 returns appropriate error detail."""
        r = client.post("/items", json={"name": "bad", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_negative_price_returns_error_detail(self):
        """Test that negative price returns error detail."""
        r = client.post("/items", json={"name": "bad", "price": -5.0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"


class TestCreateItemNameValidation:
    """Test name field validation for create_item endpoint."""

    @pytest.mark.parametrize("name", [
        "book",
        "a",
        "Product 123",
        "item with spaces",
    ])
    def test_create_item_with_valid_names(self, name):
        """Test that various valid names are accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize("name", [
        "A" * 100,
        "Very Long Product Name " * 5,
    ])
    def test_create_item_with_long_names(self, name):
        """Test that long names are handled correctly."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize("name", [
        "item!@#$",
        "item-with-dashes",
        "item_with_underscores",
        "UPPERCASE_ITEM",
        "123numeric",
    ])
    def test_create_item_with_special_characters(self, name):
        """Test that special characters and various formats are accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestCreateItemRequiredFields:
    """Test required field validation."""

    def test_create_item_missing_name_returns_error(self):
        """Test that missing name field returns validation error."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        assert "name" in str(r.json()).lower()

    def test_create_item_missing_price_returns_error(self):
        """Test that missing price field returns validation error."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422
        assert "price" in str(r.json()).lower()

    def test_create_item_empty_json_returns_error(self):
        """Test that empty JSON object returns validation error."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_create_item_with_extra_fields(self):
        """Test that extra fields are accepted (but ignored)."""
        r = client.post("/items", json={
            "name": "item",
            "price": 10.0,
            "extra_field": "ignored",
            "another": 123
        })
        assert r.status_code == 200
        assert r.json()["name"] == "item"
        assert r.json()["price"] == 10.0


class TestCreateItemResponseStructure:
    """Test response structure and field types."""

    def test_create_item_response_has_id_field(self):
        """Test that response includes id field."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert "id" in r.json()

    def test_create_item_response_has_name_field(self):
        """Test that response includes name field."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert "name" in r.json()

    def test_create_item_response_has_price_field(self):
        """Test that response includes price field."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert "price" in r.json()

    def test_create_item_response_id_is_integer(self):
        """Test that id field is an integer."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert isinstance(r.json()["id"], int)

    def test_create_item_response_name_is_string(self):
        """Test that name field is a string."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert isinstance(r.json()["name"], str)

    def test_create_item_response_price_is_float(self):
        """Test that price field is a number."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert isinstance(r.json()["price"], (int, float))


class TestCreateItemErrorHandling:
    """Test error handling and error messages."""

    def test_create_item_invalid_json_syntax(self):
        """Test that invalid JSON is handled properly."""
        r = client.post("/items", content="not json", headers={"Content-Type": "application/json"})
        assert r.status_code == 422

    def test_create_item_null_name_returns_error(self):
        """Test that null name returns validation error."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422

    def test_create_item_null_price_returns_error(self):
        """Test that null price returns validation error."""
        r = client.post("/items", json={"name": "item", "price": None})
        assert r.status_code == 422

    def test_create_item_string_price_returns_error(self):
        """Test that string price returns validation error."""
        r = client.post("/items", json={"name": "item", "price": "ten"})
        assert r.status_code == 422

    def test_create_item_numeric_name_accepted(self):
        """Test that numeric names are accepted."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # Pydantic coerces to string
        assert r.status_code == 200


class TestCreateItemEdgeCases:
    """Test edge cases and special scenarios."""

    def test_create_item_float_precision(self):
        """Test that float prices maintain precision."""
        price = 19.99
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_create_item_very_large_price(self):
        """Test that very large prices are handled."""
        price = 1e15
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_create_item_scientific_notation_price(self):
        """Test that scientific notation is parsed correctly."""
        r = client.post("/items", json={"name": "item", "price": 1e2})
        assert r.status_code == 200
        assert r.json()["price"] == 100.0

    def test_create_item_multiple_in_sequence(self):
        """Test multiple item creations in sequence."""
        for i in range(5):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
            assert r.json()["id"] == 1  # Same ID returned each time
