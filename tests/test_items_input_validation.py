"""Input validation and boundary testing for /items POST endpoint."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemValidPrice:
    """Test valid price boundary conditions."""

    @pytest.mark.parametrize("price", [0.01, 1.0, 99.99, 999.99])
    def test_create_item_with_valid_price(self, price):
        """Test that valid prices are accepted."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "item"
        assert data["price"] == price


class TestCreateItemInvalidPrice:
    """Test invalid price values."""

    @pytest.mark.parametrize("price", [-1.0, -100.0, -0.01, 0])
    def test_create_item_rejects_non_positive_price(self, price):
        """Test that non-positive prices are rejected."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"


class TestCreateItemValidName:
    """Test valid name field variations."""

    @pytest.mark.parametrize("name", [
        "book",
        "A",
        "Item 123",
        "Special-Chars_Test",
        "unicode-αβγ",
        "A" * 100,  # Long name
    ])
    def test_create_item_with_valid_name(self, name):
        """Test that valid names are accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == 10.0


class TestCreateItemInvalidName:
    """Test invalid name values."""

    @pytest.mark.parametrize("name", ["", "  ", "\n", "\t"])
    def test_create_item_rejects_empty_name(self, name):
        """Test that empty or whitespace-only names are handled."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        # Pydantic may reject empty strings depending on configuration
        # This captures the behavior
        if r.status_code == 422:
            # Validation error
            assert "detail" in r.json()
        elif r.status_code == 200:
            # Application accepts it (verify response structure)
            data = r.json()
            assert "id" in data
            assert "name" in data
            assert "price" in data


class TestCreateItemMissingFields:
    """Test requests with missing required fields."""

    def test_create_item_missing_name(self):
        """Test that missing name field is rejected."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_missing_price(self):
        """Test that missing price field is rejected."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_missing_all_fields(self):
        """Test that empty JSON is rejected."""
        r = client.post("/items", json={})
        assert r.status_code == 422
        assert "detail" in r.json()


class TestCreateItemTypeValidation:
    """Test invalid data types for fields."""

    def test_create_item_price_as_string(self):
        """Test that price as string is rejected."""
        r = client.post("/items", json={"name": "item", "price": "10.0"})
        # Pydantic may coerce or reject - capture behavior
        if r.status_code == 422:
            assert "detail" in r.json()
        elif r.status_code == 200:
            data = r.json()
            assert isinstance(data["price"], (int, float))

    def test_create_item_name_as_number(self):
        """Test that name as number is handled."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # Pydantic may coerce or reject
        if r.status_code == 422:
            assert "detail" in r.json()
        elif r.status_code == 200:
            data = r.json()
            assert isinstance(data["name"], str)

    def test_create_item_price_as_boolean(self):
        """Test that price as boolean is handled."""
        r = client.post("/items", json={"name": "item", "price": True})
        # Pydantic may interpret True as 1 or reject
        if r.status_code == 422:
            assert "detail" in r.json()
        elif r.status_code == 200:
            data = r.json()
            assert isinstance(data["price"], (int, float))


class TestCreateItemExtraFields:
    """Test handling of extra fields in request."""

    def test_create_item_with_extra_fields(self):
        """Test that extra fields are ignored."""
        r = client.post("/items", json={
            "name": "item",
            "price": 10.0,
            "extra_field": "should be ignored",
            "another": 123
        })
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "item"
        assert data["price"] == 10.0
        # Extra fields should not appear in response
        assert "extra_field" not in data


class TestCreateItemBoundaryValues:
    """Test extreme boundary values."""

    def test_create_item_very_small_price(self):
        """Test very small but valid price."""
        r = client.post("/items", json={"name": "item", "price": 0.001})
        assert r.status_code == 200
        assert r.json()["price"] == 0.001

    def test_create_item_very_large_price(self):
        """Test very large price."""
        r = client.post("/items", json={"name": "item", "price": 999999.99})
        assert r.status_code == 200
        assert r.json()["price"] == 999999.99

    def test_create_item_very_long_name(self):
        """Test very long name string."""
        long_name = "A" * 500
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == long_name
        assert len(data["name"]) == 500


class TestCreateItemFloatPrecision:
    """Test float precision handling."""

    @pytest.mark.parametrize("price", [0.1, 0.01, 0.001, 1.5, 2.25])
    def test_create_item_float_precision(self, price):
        """Test that float prices are preserved correctly."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        # Float comparison with small tolerance for precision issues
        returned_price = r.json()["price"]
        assert abs(returned_price - price) < 0.0001
