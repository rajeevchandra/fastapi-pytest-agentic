"""Input validation and boundary testing for /items endpoint."""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation on POST /items."""

    @pytest.mark.parametrize("price,expected_status", [
        (0.01, 200),        # minimum valid
        (0.1, 200),         # small valid
        (1.0, 200),         # normal valid
        (100.0, 200),       # large valid
        (999999.99, 200),   # very large valid
        (0, 400),           # zero (invalid)
        (-0.01, 400),       # negative small
        (-1.0, 400),        # negative normal
        (-100.0, 400),      # negative large
    ])
    def test_create_item_price_boundary(self, price, expected_status):
        """Test various price boundary conditions."""
        response = client.post("/items", json={"name": "test", "price": price})
        assert response.status_code == expected_status
        if expected_status == 400:
            assert "price must be > 0" in response.json()["detail"]


class TestCreateItemNameValidation:
    """Test name field validation on POST /items."""

    @pytest.mark.parametrize("name,expected_status", [
        ("a", 200),                                    # single char
        ("Book", 200),                                 # normal
        ("Very Long Product Name", 200),               # with spaces
        ("test-product-123", 200),                     # alphanumeric + dash
        ("product_with_underscore", 200),              # with underscore
        ("Ñoño", 200),                                 # unicode
        ("Test™", 200),                                # special unicode
        ("a" * 100, 200),                              # very long string
        ("Book " * 50, 200),                           # very long with repeats
    ])
    def test_create_item_name_variations(self, name, expected_status):
        """Test various name field values."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        assert response.status_code == expected_status
        if expected_status == 200:
            assert response.json()["name"] == name


class TestCreateItemMissingFields:
    """Test missing required fields on POST /items."""

    def test_create_item_missing_name(self):
        """Missing name field should fail."""
        response = client.post("/items", json={"price": 10.0})
        assert response.status_code == 422

    def test_create_item_missing_price(self):
        """Missing price field should fail."""
        response = client.post("/items", json={"name": "test"})
        assert response.status_code == 422

    def test_create_item_empty_body(self):
        """Empty JSON body should fail."""
        response = client.post("/items", json={})
        assert response.status_code == 422


class TestCreateItemTypeValidation:
    """Test type validation on POST /items."""

    def test_create_item_price_as_string(self):
        """Price as string should fail validation."""
        response = client.post("/items", json={"name": "test", "price": "10.0"})
        assert response.status_code == 422

    def test_create_item_name_as_number(self):
        """Name as number should fail validation."""
        response = client.post("/items", json={"name": 123, "price": 10.0})
        assert response.status_code == 422

    def test_create_item_null_price(self):
        """Null price should fail validation."""
        response = client.post("/items", json={"name": "test", "price": None})
        assert response.status_code == 422

    def test_create_item_null_name(self):
        """Null name should fail validation."""
        response = client.post("/items", json={"name": None, "price": 10.0})
        assert response.status_code == 422


class TestCreateItemEdgeCases:
    """Test edge cases for POST /items."""

    def test_create_item_empty_string_name(self):
        """Empty string name might still be accepted by Pydantic, test response."""
        response = client.post("/items", json={"name": "", "price": 10.0})
        # Pydantic may accept empty string, just verify response
        assert response.status_code in [200, 422]

    def test_create_item_whitespace_name(self):
        """Whitespace-only name."""
        response = client.post("/items", json={"name": "   ", "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == "   "

    def test_create_item_extra_fields_ignored(self):
        """Extra fields in request should be ignored by Pydantic."""
        response = client.post(
            "/items",
            json={"name": "test", "price": 10.0, "extra_field": "ignored"}
        )
        assert response.status_code == 200
        assert "extra_field" not in response.json()
