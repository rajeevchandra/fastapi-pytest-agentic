import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price validation for POST /items endpoint."""

    @pytest.mark.parametrize(
        "price,expected_status,error_detail",
        [
            (0, 400, "price must be > 0"),
            (-1, 400, "price must be > 0"),
            (-100.5, 400, "price must be > 0"),
            (-0.01, 400, "price must be > 0"),
        ],
    )
    def test_price_non_positive_values(self, price, expected_status, error_detail):
        """Test that non-positive prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == expected_status
        assert r.json()["detail"] == error_detail

    @pytest.mark.parametrize(
        "price",
        [0.01, 0.1, 1, 10.5, 100, 999.99, 9999.99, 100000.0],
    )
    def test_price_positive_values(self, price):
        """Test that positive prices are accepted."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price


class TestCreateItemNameValidation:
    """Test name validation for POST /items endpoint."""

    @pytest.mark.parametrize(
        "name",
        [
            "a",
            "book",
            "A",
            "Product 1",
            "item-with-dashes",
            "item_with_underscores",
            "123",
            "special!@#$%",
            "a" * 255,  # Long name
        ],
    )
    def test_name_various_values(self, name):
        """Test that various name values are accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["id"] == 1
        assert data["price"] == 10.0


class TestCreateItemMissingFields:
    """Test missing required fields for POST /items endpoint."""

    def test_missing_name_field(self):
        """Test that missing 'name' field returns validation error."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422  # Unprocessable Entity

    def test_missing_price_field(self):
        """Test that missing 'price' field returns validation error."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_missing_all_fields(self):
        """Test that missing all fields returns validation error."""
        r = client.post("/items", json={})
        assert r.status_code == 422


class TestCreateItemInvalidTypes:
    """Test invalid data types for POST /items endpoint."""

    def test_price_as_string(self):
        """Test that price can be coerced from string."""
        r = client.post("/items", json={"name": "test", "price": "10.5"})
        # Pydantic should coerce string to float
        assert r.status_code == 200
        assert r.json()["price"] == 10.5

    def test_price_as_string_invalid(self):
        """Test that invalid string price returns error."""
        r = client.post("/items", json={"name": "test", "price": "not_a_number"})
        assert r.status_code == 422

    def test_name_as_number(self):
        """Test that name can be coerced from number."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # Pydantic should coerce number to string
        assert r.status_code == 200
        assert r.json()["name"] == "123"

    def test_price_as_null(self):
        """Test that null price returns error."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422


class TestCreateItemResponseStructure:
    """Test response structure for POST /items endpoint."""

    def test_response_has_all_fields(self):
        """Test that response includes all required fields."""
        r = client.post("/items", json={"name": "book", "price": 19.99})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert len(data) == 3  # Only these three fields

    def test_response_field_types(self):
        """Test that response fields have correct types."""
        r = client.post("/items", json={"name": "book", "price": 19.99})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_response_id_is_always_one(self):
        """Test that created item ID is always 1."""
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": float(i + 1)})
            assert r.status_code == 200
            assert r.json()["id"] == 1


class TestCreateItemErrorHandling:
    """Test error handling for POST /items endpoint."""

    def test_error_response_format(self):
        """Test that error responses have correct format."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_validation_error_format(self):
        """Test that validation errors have detail field."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data
        # detail should be a list of error objects or a string
        assert isinstance(data["detail"], (list, str))

    @pytest.mark.parametrize(
        "invalid_price",
        [-1000, -999.99, -0.001],
    )
    def test_negative_price_detailed_error(self, invalid_price):
        """Test that negative prices produce consistent error messages."""
        r = client.post("/items", json={"name": "test", "price": invalid_price})
        assert r.status_code == 400
        assert "detail" in r.json()
        assert "price" in r.json()["detail"].lower()
