import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price validation for create_item endpoint."""

    @pytest.mark.parametrize(
        "price,expected_status",
        [
            (0, 400),  # Zero price (invalid)
            (-1.0, 400),  # Negative price (invalid)
            (-100.50, 400),  # Large negative price (invalid)
            (0.001, 200),  # Very small positive price (valid)
            (0.01, 200),  # Small positive price (valid)
            (1.0, 200),  # Normal price (valid)
            (100.0, 200),  # Large price (valid)
            (9999999.99, 200),  # Very large price (valid)
            (1e10, 200),  # Extreme large price (valid)
        ],
    )
    def test_create_item_price_boundaries(self, price, expected_status):
        """Test various price values at boundaries."""
        r = client.post("/items", json={"name": "test_item", "price": price})
        assert r.status_code == expected_status
        if expected_status == 200:
            data = r.json()
            assert data["price"] == price


class TestCreateItemNameValidation:
    """Test name validation for create_item endpoint."""

    @pytest.mark.parametrize(
        "name,expected_status",
        [
            ("", 422),  # Empty string (invalid - Pydantic validates non-empty string)
            ("a", 200),  # Single character (valid)
            ("valid_name", 200),  # Normal name (valid)
            ("Item with spaces", 200),  # Name with spaces (valid)
            ("Special-Characters_123", 200),  # Name with special chars (valid)
            ("name" * 100, 200),  # Very long name (valid)
            ("日本語", 200),  # Unicode characters (valid)
            ("name@with#symbols", 200),  # Symbols (valid)
        ],
    )
    def test_create_item_name_variations(self, name, expected_status):
        """Test various name values."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == expected_status
        if expected_status == 200:
            data = r.json()
            assert data["name"] == name


class TestCreateItemMissingFields:
    """Test missing required fields for create_item endpoint."""

    def test_create_item_missing_name(self):
        """Test POST with missing name field."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_create_item_missing_price(self):
        """Test POST with missing price field."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422

    def test_create_item_missing_both_fields(self):
        """Test POST with empty body."""
        r = client.post("/items", json={})
        assert r.status_code == 422


class TestCreateItemInvalidTypes:
    """Test invalid data types for create_item endpoint."""

    def test_create_item_price_as_string(self):
        """Test POST with price as string."""
        r = client.post("/items", json={"name": "item", "price": "10.0"})
        # FastAPI/Pydantic coerces strings to floats if valid
        assert r.status_code in [200, 422]

    def test_create_item_price_as_none(self):
        """Test POST with price as null."""
        r = client.post("/items", json={"name": "item", "price": None})
        assert r.status_code == 422

    def test_create_item_name_as_number(self):
        """Test POST with name as number."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # FastAPI/Pydantic coerces numbers to strings
        assert r.status_code in [200, 422]

    def test_create_item_name_as_none(self):
        """Test POST with name as null."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422


class TestCreateItemSuccessVariations:
    """Test successful creation with various valid inputs."""

    @pytest.mark.parametrize(
        "name,price",
        [
            ("Book", 15.99),
            ("Pen", 0.99),
            ("Laptop", 999.99),
            ("A", 0.01),
            ("Product " + "x" * 50, 50.0),
        ],
    )
    def test_create_item_various_valid_inputs(self, name, price):
        """Test successful creation with various valid inputs."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price
        assert "id" in data
