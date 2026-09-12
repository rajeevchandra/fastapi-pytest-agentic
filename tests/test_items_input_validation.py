from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation in create_item endpoint."""

    @pytest.mark.parametrize("price", [-100, -1, 0])
    def test_create_item_rejects_non_positive_prices(self, price):
        """Negative and zero prices should return 400."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [0.01, 1, 10.5, 999.99, 1e10])
    def test_create_item_accepts_positive_prices(self, price):
        """Positive prices should be accepted."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_create_item_price_type_coercion(self):
        """Pydantic should coerce string prices to float."""
        r = client.post("/items", json={"name": "test", "price": "10.5"})
        assert r.status_code == 200
        assert r.json()["price"] == 10.5


class TestCreateItemNameValidation:
    """Test name field validation in create_item endpoint."""

    def test_create_item_accepts_normal_name(self):
        """Normal names should be accepted."""
        r = client.post("/items", json={"name": "book", "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == "book"

    def test_create_item_accepts_long_name(self):
        """Long names should be accepted."""
        long_name = "x" * 1000
        r = client.post("/items", json={"name": long_name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_create_item_accepts_special_chars_in_name(self):
        """Names with special characters should be accepted."""
        r = client.post("/items", json={"name": "book-2024™", "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == "book-2024™"

    def test_create_item_accepts_unicode_name(self):
        """Unicode names should be accepted."""
        r = client.post("/items", json={"name": "本書", "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == "本書"


class TestCreateItemMissingFields:
    """Test missing required fields in create_item endpoint."""

    def test_create_item_missing_name(self):
        """Missing name field should return 422."""
        r = client.post("/items", json={"price": 10})
        assert r.status_code == 422

    def test_create_item_missing_price(self):
        """Missing price field should return 422."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_create_item_missing_all_fields(self):
        """Missing all fields should return 422."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_create_item_null_name(self):
        """Null name should return 422."""
        r = client.post("/items", json={"name": None, "price": 10})
        assert r.status_code == 422

    def test_create_item_null_price(self):
        """Null price should return 422."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422


class TestCreateItemInvalidTypes:
    """Test invalid field types in create_item endpoint."""

    def test_create_item_price_as_array(self):
        """Array price should return 422."""
        r = client.post("/items", json={"name": "test", "price": [1, 2]})
        assert r.status_code == 422

    def test_create_item_price_as_object(self):
        """Object price should return 422."""
        r = client.post("/items", json={"name": "test", "price": {"val": 10}})
        assert r.status_code == 422

    def test_create_item_name_as_number(self):
        """Numeric name can be coerced to string by Pydantic."""
        r = client.post("/items", json={"name": 123, "price": 10})
        # Pydantic coerces int to str
        assert r.status_code == 200

    def test_create_item_name_as_array(self):
        """Array name should return 422."""
        r = client.post("/items", json={"name": [1, 2], "price": 10})
        assert r.status_code == 422


class TestCreateItemResponseStructure:
    """Test response structure of create_item endpoint."""

    def test_create_item_response_has_required_fields(self):
        """Response should contain id, name, and price fields."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_id_is_one(self):
        """Response id should be 1."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.json()["id"] == 1

    def test_create_item_response_echoes_input_name(self):
        """Response name should match input."""
        test_name = "unique-book-name"
        r = client.post("/items", json={"name": test_name, "price": 10})
        assert r.json()["name"] == test_name

    def test_create_item_response_echoes_input_price(self):
        """Response price should match input."""
        test_price = 99.99
        r = client.post("/items", json={"name": "test", "price": test_price})
        assert r.json()["price"] == test_price


class TestCreateItemErrorHandling:
    """Test error handling in create_item endpoint."""

    def test_create_item_error_response_has_detail(self):
        """Error responses should have detail field."""
        r = client.post("/items", json={"name": "test", "price": -1})
        assert "detail" in r.json()

    def test_create_item_error_response_is_string(self):
        """Error detail should be a string."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert isinstance(r.json()["detail"], str)

    def test_create_item_422_response_is_json(self):
        """422 responses should be valid JSON."""
        r = client.post("/items", json={"price": 10})
        assert r.headers["content-type"] == "application/json"
        # Should not raise
        data = r.json()
        assert isinstance(data, dict)
