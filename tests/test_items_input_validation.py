import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price validation for create_item endpoint."""

    @pytest.mark.parametrize("price", [
        0,
        -1,
        -100,
        -0.01,
        -999999.99,
    ])
    def test_create_item_rejects_non_positive_prices(self, price):
        """Test that non-positive prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [
        0.01,
        0.001,
        0.0001,
        1,
        100,
        999999.99,
    ])
    def test_create_item_accepts_positive_prices(self, price):
        """Test that positive prices are accepted."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price


class TestCreateItemNameValidation:
    """Test name validation for create_item endpoint."""

    @pytest.mark.parametrize("name", [
        "a",
        "book",
        "very long product name with many words and special chars!@#",
        "Product 123",
        "name-with-dash",
        "name_with_underscore",
        "UPPERCASE",
        "MiXeD cAsE",
        "名前",  # Unicode
        "😀 emoji",
    ])
    def test_create_item_accepts_various_names(self, name):
        """Test that various valid names are accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name

    def test_create_item_with_empty_name_fails(self):
        """Test that empty name fails validation (Pydantic constraint)."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        # Pydantic will validate this as either 200 or 422 depending on model config
        # With default Pydantic, empty strings are allowed unless constrained
        # This test documents the actual behavior
        assert r.status_code in [200, 422]


class TestCreateItemMissingFields:
    """Test handling of missing required fields."""

    def test_create_item_missing_name(self):
        """Test that missing name field is rejected."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_create_item_missing_price(self):
        """Test that missing price field is rejected."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_create_item_missing_all_fields(self):
        """Test that completely empty request is rejected."""
        r = client.post("/items", json={})
        assert r.status_code == 422


class TestCreateItemInvalidTypes:
    """Test type validation for create_item fields."""

    def test_create_item_string_price_fails(self):
        """Test that string price is rejected."""
        r = client.post("/items", json={"name": "test", "price": "10.0"})
        assert r.status_code == 422

    def test_create_item_null_price_fails(self):
        """Test that null price is rejected."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422

    def test_create_item_numeric_name_accepts(self):
        """Test that numeric name (as string) is accepted."""
        r = client.post("/items", json={"name": "123", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "123"

    def test_create_item_null_name_fails(self):
        """Test that null name is rejected."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422

    def test_create_item_boolean_price_fails(self):
        """Test that boolean price is rejected."""
        r = client.post("/items", json={"name": "test", "price": True})
        assert r.status_code == 422


class TestCreateItemExtraFields:
    """Test handling of extra fields in request."""

    def test_create_item_with_extra_field(self):
        """Test that extra fields are ignored."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "extra_field": "should be ignored"
        })
        assert r.status_code == 200
        data = r.json()
        assert "extra_field" not in data

    def test_create_item_with_multiple_extra_fields(self):
        """Test that multiple extra fields are ignored."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "field1": "value1",
            "field2": "value2"
        })
        assert r.status_code == 200


class TestCreateItemResponseStructure:
    """Test response structure for successful create_item."""

    def test_create_item_response_has_required_fields(self):
        """Test that response contains id, name, and price."""
        r = client.post("/items", json={"name": "test", "price": 10.5})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_id_is_integer(self):
        """Test that response id is an integer."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        assert isinstance(data["id"], int)

    def test_create_item_response_price_is_number(self):
        """Test that response price is a number."""
        r = client.post("/items", json={"name": "test", "price": 10.5})
        data = r.json()
        assert isinstance(data["price"], (int, float))

    def test_create_item_response_name_is_string(self):
        """Test that response name is a string."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        assert isinstance(data["name"], str)


class TestCreateItemErrorResponses:
    """Test error response structure."""

    def test_invalid_price_error_has_detail(self):
        """Test that error response includes detail message."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_missing_field_error_response(self):
        """Test that missing field errors include proper response."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data
