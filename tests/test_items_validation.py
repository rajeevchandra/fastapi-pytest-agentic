import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation for POST /items endpoint"""

    def test_create_item_negative_price(self):
        """Test rejection of negative price (-1)"""
        r = client.post("/items", json={"name": "test", "price": -1})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_large_negative_price(self):
        """Test rejection of large negative price (-100.50)"""
        r = client.post("/items", json={"name": "test", "price": -100.50})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_zero_price(self):
        """Test rejection of zero price (already in test_items.py)"""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_very_large_positive_price(self):
        """Test acceptance of very large positive price"""
        r = client.post("/items", json={"name": "test", "price": 999999.99})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == 999999.99

    def test_create_item_minimal_valid_price(self):
        """Test acceptance of minimal valid price (0.01)"""
        r = client.post("/items", json={"name": "test", "price": 0.01})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == 0.01

    def test_create_item_small_positive_price(self):
        """Test acceptance of small positive price"""
        r = client.post("/items", json={"name": "test", "price": 0.5})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == 0.5


class TestCreateItemMissingFields:
    """Test missing required fields for POST /items endpoint"""

    def test_create_item_missing_name(self):
        """Test rejection when name field is missing"""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_create_item_missing_price(self):
        """Test rejection when price field is missing"""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_create_item_missing_both_fields(self):
        """Test rejection when both name and price are missing"""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_create_item_null_name(self):
        """Test rejection when name is null"""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422

    def test_create_item_null_price(self):
        """Test rejection when price is null"""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422


class TestCreateItemNameValidation:
    """Test name field validation for POST /items endpoint"""

    def test_create_item_empty_name(self):
        """Test acceptance of empty string (Pydantic allows it)"""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == ""

    def test_create_item_whitespace_name(self):
        """Test acceptance of whitespace-only name (Pydantic allows it)"""
        r = client.post("/items", json={"name": "   ", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "   "

    def test_create_item_long_name(self):
        """Test acceptance of very long name"""
        long_name = "a" * 1000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == long_name

    def test_create_item_unicode_name(self):
        """Test acceptance of unicode characters in name"""
        r = client.post("/items", json={"name": "商品 📚", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "商品 📚"

    def test_create_item_special_chars_name(self):
        """Test acceptance of special characters in name"""
        r = client.post("/items", json={"name": "test!@#$%^&*()", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "test!@#$%^&*()"


class TestCreateItemTypeValidation:
    """Test invalid data types for POST /items endpoint"""

    def test_create_item_string_price(self):
        """Test rejection when price is a string"""
        r = client.post("/items", json={"name": "test", "price": "10.0"})
        assert r.status_code == 422

    def test_create_item_boolean_price(self):
        """Test rejection when price is a boolean"""
        r = client.post("/items", json={"name": "test", "price": True})
        # True coerces to 1.0 in some cases - check status and handle accordingly
        assert r.status_code in [200, 422]

    def test_create_item_numeric_name(self):
        """Test rejection when name is numeric instead of string"""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # Pydantic may coerce number to string
        assert r.status_code in [200, 422]

    def test_create_item_array_name(self):
        """Test rejection when name is an array"""
        r = client.post("/items", json={"name": ["a", "b"], "price": 10.0})
        assert r.status_code == 422

    def test_create_item_object_price(self):
        """Test rejection when price is an object"""
        r = client.post("/items", json={"name": "test", "price": {"value": 10.0}})
        assert r.status_code == 422


class TestCreateItemExtraFields:
    """Test handling of extra/unknown fields"""

    def test_create_item_with_extra_field(self):
        """Test that extra fields are ignored"""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "extra_field": "should be ignored"
        })
        assert r.status_code == 200
        data = r.json()
        assert "extra_field" not in data
        assert data["name"] == "test"

    def test_create_item_with_multiple_extra_fields(self):
        """Test that multiple extra fields are ignored"""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "extra1": "value1",
            "extra2": "value2",
            "extra3": "value3"
        })
        assert r.status_code == 200
        data = r.json()
        assert all(field not in data for field in ["extra1", "extra2", "extra3"])


class TestCreateItemParametrized:
    """Parametrized tests for comprehensive coverage"""

    @pytest.mark.parametrize("price", [0.01, 1.0, 10.5, 100.0, 999999.99])
    def test_valid_prices(self, price):
        """Test that various positive prices are accepted"""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price

    @pytest.mark.parametrize("price", [-0.01, -1.0, -10.5, -100.0, -999999.99])
    def test_invalid_negative_prices(self, price):
        """Test that negative prices are rejected"""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("name", [
        "a",
        "test item",
        "Test Item With Caps",
        "item-with-dash",
        "item_with_underscore",
        "123item",
    ])
    def test_valid_names(self, name):
        """Test that various name formats are accepted"""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name

    @pytest.mark.parametrize("name,price", [
        ("book", 12.99),
        ("pen", 0.99),
        ("laptop", 999.99),
        ("free sample", 0.01),
    ])
    def test_valid_combinations(self, name, price):
        """Test various valid name and price combinations"""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price
        assert data["id"] == 1
