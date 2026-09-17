import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price validation for create_item endpoint."""

    @pytest.mark.parametrize("price", [-100, -1, -0.01])
    def test_create_item_rejects_negative_prices(self, price):
        """Negative prices should be rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_rejects_zero_price(self):
        """Zero price should be rejected."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [0.01, 1, 100, 999999.99])
    def test_create_item_accepts_positive_prices(self, price):
        """Positive prices should be accepted."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price
        assert data["name"] == "item"

    @pytest.mark.parametrize("price", [1e10, 9999999.99])
    def test_create_item_accepts_very_large_prices(self, price):
        """Very large prices should be accepted."""
        r = client.post("/items", json={"name": "expensive", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price


class TestCreateItemNameValidation:
    """Test name validation for create_item endpoint."""

    def test_create_item_with_normal_name(self):
        """Normal name should be accepted."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "book"

    @pytest.mark.parametrize("name", ["a", "ab", "A", "ABC123"])
    def test_create_item_with_short_names(self, name):
        """Short names should be accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_with_long_name(self):
        """Long name should be accepted."""
        long_name = "a" * 500
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    @pytest.mark.parametrize("name", ["name with spaces", "name-with-dashes", "name_with_underscores"])
    def test_create_item_with_special_characters(self, name):
        """Names with special characters should be accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize("name", ["café", "文字", "emoji😊"])
    def test_create_item_with_unicode_names(self, name):
        """Unicode names should be accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestCreateItemMissingFields:
    """Test missing field validation for create_item endpoint."""

    def test_create_item_missing_name(self):
        """Missing name field should be rejected with 422."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_create_item_missing_price(self):
        """Missing price field should be rejected with 422."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_create_item_empty_json(self):
        """Empty JSON body should be rejected with 422."""
        r = client.post("/items", json={})
        assert r.status_code == 422


class TestCreateItemTypeValidation:
    """Test type validation for create_item endpoint."""

    def test_create_item_price_as_string(self):
        """Price as string should be converted or rejected."""
        r = client.post("/items", json={"name": "test", "price": "10.0"})
        # Pydantic should handle type coercion or reject
        if r.status_code == 200:
            assert float(r.json()["price"]) == 10.0
        else:
            assert r.status_code == 422

    def test_create_item_name_as_number(self):
        """Name as number should be converted or rejected."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # Pydantic should handle type coercion or reject
        if r.status_code == 200:
            assert r.json()["name"] == "123"
        else:
            assert r.status_code == 422

    def test_create_item_with_null_name(self):
        """Null name should be rejected."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422

    def test_create_item_with_null_price(self):
        """Null price should be rejected."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422


class TestCreateItemExtraFields:
    """Test handling of extra fields in create_item endpoint."""

    def test_create_item_with_extra_fields(self):
        """Extra fields should be ignored or rejected depending on Pydantic config."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "extra_field": "value"
        })
        # Should still succeed as Pydantic ignores extra fields by default
        assert r.status_code == 200
        assert r.json()["name"] == "test"

    def test_create_item_with_multiple_extra_fields(self):
        """Multiple extra fields should be handled."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "description": "test description",
            "tags": ["tag1", "tag2"]
        })
        assert r.status_code == 200
        assert r.json()["price"] == 10.0


class TestCreateItemResponseStructure:
    """Test response structure from create_item endpoint."""

    def test_create_item_response_has_required_fields(self):
        """Response should contain id, name, and price."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_id_type(self):
        """Response id should be an integer."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert isinstance(r.json()["id"], int)

    def test_create_item_response_name_type(self):
        """Response name should match input name."""
        name = "test_item"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name
        assert isinstance(r.json()["name"], str)

    def test_create_item_response_price_type(self):
        """Response price should be a number."""
        r = client.post("/items", json={"name": "test", "price": 10.5})
        assert r.status_code == 200
        assert isinstance(r.json()["price"], (int, float))
