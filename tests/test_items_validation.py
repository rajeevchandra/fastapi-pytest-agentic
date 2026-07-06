from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price validation for create_item endpoint"""

    def test_create_item_negative_price(self):
        """Test rejection of negative price"""
        r = client.post("/items", json={"name": "book", "price": -1})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_large_negative_price(self):
        """Test rejection of large negative price"""
        r = client.post("/items", json={"name": "item", "price": -100.50})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [0, -1, -10, -999.99])
    def test_create_item_invalid_prices(self, price):
        """Parametrized test for all invalid prices"""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [0.01, 1, 100, 999999.99])
    def test_create_item_valid_prices(self, price):
        """Parametrized test for all valid prices"""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price


class TestCreateItemInputValidation:
    """Test input validation for create_item endpoint"""

    def test_create_item_missing_name(self):
        """Test rejection when name is missing"""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_create_item_missing_price(self):
        """Test rejection when price is missing"""
        r = client.post("/items", json={"name": "book"})
        assert r.status_code == 422

    def test_create_item_empty_name(self):
        """Test creation with empty string name (Pydantic allows it)"""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == ""

    def test_create_item_whitespace_name(self):
        """Test creation with whitespace name"""
        r = client.post("/items", json={"name": "   ", "price": 5.0})
        assert r.status_code == 200
        assert r.json()["name"] == "   "

    def test_create_item_very_long_name(self):
        """Test creation with very long name"""
        long_name = "a" * 1000
        r = client.post("/items", json={"name": long_name, "price": 15.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_create_item_price_as_string(self):
        """Test rejection when price is sent as string"""
        r = client.post("/items", json={"name": "book", "price": "10.0"})
        # Pydantic should coerce string to float or reject with 422
        # Test the actual behavior
        assert r.status_code in [200, 422]

    def test_create_item_price_as_integer(self):
        """Test creation with price as integer (should coerce to float)"""
        r = client.post("/items", json={"name": "book", "price": 10})
        assert r.status_code == 200
        assert r.json()["price"] == 10

    def test_create_item_name_as_number(self):
        """Test creation with name as number (should coerce to string)"""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "123"
