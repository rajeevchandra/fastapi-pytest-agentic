from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation for create item endpoint."""

    @pytest.mark.parametrize("price", [-100, -1, 0])
    def test_negative_and_zero_prices_rejected(self, price):
        """Verify that non-positive prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    @pytest.mark.parametrize("price", [0.01, 0.1, 1.0, 10.5, 99.99, 1000.0, 999999.99])
    def test_positive_prices_accepted(self, price):
        """Verify that positive prices are accepted."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_price_field_required(self):
        """Verify that price field is required."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        errors = r.json()["detail"]
        assert any(e["loc"][1] == "price" for e in errors)

    def test_price_must_be_number(self):
        """Verify that price must be a valid number."""
        r = client.post("/items", json={"name": "test", "price": "not_a_number"})
        assert r.status_code == 422
        errors = r.json()["detail"]
        assert any(e["loc"][1] == "price" for e in errors)


class TestCreateItemNameValidation:
    """Test name field validation for create item endpoint."""

    @pytest.mark.parametrize("name", ["", " ", "  "])
    def test_empty_and_whitespace_names_accepted(self, name):
        """Verify that empty/whitespace names are accepted by Pydantic."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200

    @pytest.mark.parametrize("name", [
        "a",
        "book",
        "Advanced Python Programming",
        "Item-123",
        "special_chars!@#$",
    ])
    def test_various_valid_names(self, name):
        """Verify that various valid names are accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_long_name_accepted(self):
        """Verify that long names are accepted."""
        long_name = "x" * 500
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_unicode_name_accepted(self):
        """Verify that unicode characters in names are accepted."""
        unicode_name = "café_naïve_日本語"
        r = client.post("/items", json={"name": unicode_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == unicode_name

    def test_name_field_required(self):
        """Verify that name field is required."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        errors = r.json()["detail"]
        assert any(e["loc"][1] == "name" for e in errors)


class TestCreateItemRequestValidation:
    """Test overall request validation for create item endpoint."""

    def test_both_fields_required(self):
        """Verify that both name and price are required."""
        r = client.post("/items", json={})
        assert r.status_code == 422
        errors = r.json()["detail"]
        assert len(errors) == 2

    def test_extra_fields_ignored(self):
        """Verify that extra fields in request are ignored."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "extra_field": "ignored",
            "another": 123
        })
        assert r.status_code == 200
        assert r.json()["name"] == "test"

    def test_invalid_json(self):
        """Verify proper error for invalid JSON."""
        r = client.post("/items", content="{invalid json}")
        assert r.status_code == 422

    def test_content_type_application_json(self):
        """Verify that application/json content type works."""
        r = client.post(
            "/items",
            json={"name": "test", "price": 10.0},
            headers={"Content-Type": "application/json"}
        )
        assert r.status_code == 200


class TestCreateItemResponseStructure:
    """Test response structure for create item endpoint."""

    def test_response_contains_all_fields(self):
        """Verify response contains id, name, and price."""
        r = client.post("/items", json={"name": "test", "price": 25.5})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_response_field_types(self):
        """Verify response field types are correct."""
        r = client.post("/items", json={"name": "test", "price": 25.5})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_response_preserves_input_values(self):
        """Verify that response preserves input name and price."""
        name, price = "my_item", 42.99
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price

    def test_response_always_has_id_1(self):
        """Verify that response always returns id=1 (current implementation)."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["id"] == 1


class TestCreateItemErrorResponses:
    """Test error response structure and messages."""

    def test_price_error_has_detail(self):
        """Verify error response for invalid price has detail field."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data

    def test_validation_error_structure(self):
        """Verify validation error has standard FastAPI structure."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)

    def test_validation_error_includes_field_info(self):
        """Verify validation error includes field location."""
        r = client.post("/items", json={"name": "test", "price": "invalid"})
        assert r.status_code == 422
        errors = r.json()["detail"]
        assert any(e["loc"][1] == "price" for e in errors)
        assert any("loc" in e for e in errors)

    def test_multiple_validation_errors(self):
        """Verify multiple validation errors are all reported."""
        r = client.post("/items", json={})
        assert r.status_code == 422
        errors = r.json()["detail"]
        assert len(errors) >= 2


class TestCreateItemEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_price_boundary_exactly_zero(self):
        """Verify that exactly zero is rejected."""
        r = client.post("/items", json={"name": "test", "price": 0.0})
        assert r.status_code == 400

    def test_price_boundary_just_above_zero(self):
        """Verify that smallest positive price is accepted."""
        r = client.post("/items", json={"name": "test", "price": 0.0001})
        assert r.status_code == 200

    def test_very_large_price(self):
        """Verify that very large prices are accepted."""
        r = client.post("/items", json={"name": "test", "price": 1e10})
        assert r.status_code == 200
        assert r.json()["price"] == 1e10

    def test_scientific_notation_price(self):
        """Verify scientific notation is accepted for price."""
        r = client.post("/items", json={"name": "test", "price": 1.5e3})
        assert r.status_code == 200
        assert r.json()["price"] == 1500.0

    def test_null_price(self):
        """Verify that null price is rejected."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422

    def test_null_name(self):
        """Verify that null name is rejected."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422
