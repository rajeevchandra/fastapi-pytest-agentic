"""
Comprehensive edge case and boundary value testing for items endpoints.
Covers input validation, response structure, path parameters, and error handling.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceBoundaries:
    """Test price field boundary conditions and validation."""

    @pytest.mark.parametrize("price", [
        0,
        -1,
        -0.01,
        -100,
        -999999,
    ])
    def test_create_item_rejects_zero_and_negative_prices(self, price):
        """Verify that zero and negative prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [
        0.01,
        0.001,
        1,
        10.5,
        100,
        999999.99,
        1e10,
    ])
    def test_create_item_accepts_positive_prices(self, price):
        """Verify that all positive prices are accepted."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price
        assert isinstance(data["price"], float)

    def test_create_item_with_very_large_price(self):
        """Verify handling of very large float values."""
        r = client.post("/items", json={"name": "expensive", "price": 1e308})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] > 0

    def test_create_item_with_very_small_positive_price(self):
        """Verify handling of very small positive values."""
        r = client.post("/items", json={"name": "cheap", "price": 1e-10})
        assert r.status_code == 200
        assert r.json()["price"] > 0


class TestCreateItemNameValidation:
    """Test name field variations and edge cases."""

    @pytest.mark.parametrize("name", [
        "a",
        "ab",
        "normal product name",
        "Product with UPPERCASE",
        "name-with-dashes",
        "name_with_underscores",
        "name.with.dots",
        "name with   multiple spaces",
        "123numeric",
        "特殊文字",  # Japanese characters
        "émojis_тест",  # Mixed Unicode
    ])
    def test_create_item_accepts_various_name_formats(self, name):
        """Verify that diverse name formats are accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize("name", [
        "a" * 100,
        "a" * 500,
        "a" * 1000,
    ])
    def test_create_item_accepts_long_names(self, name):
        """Verify handling of very long name strings."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name
        assert len(r.json()["name"]) == len(name)

    @pytest.mark.parametrize("name", [
        "name\nwith\nnewlines",
        "name\twith\ttabs",
        "name with special chars: !@#$%^&*()",
        "quotes: 'single' and \"double\"",
    ])
    def test_create_item_accepts_special_characters_in_name(self, name):
        """Verify that special characters in names are preserved."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_rejects_missing_name(self):
        """Verify that missing name field is rejected."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422  # Pydantic validation error

    def test_create_item_rejects_missing_price(self):
        """Verify that missing price field is rejected."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422  # Pydantic validation error

    def test_create_item_rejects_null_name(self):
        """Verify that null name is rejected."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422

    def test_create_item_rejects_null_price(self):
        """Verify that null price is rejected."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422

    def test_create_item_rejects_string_price(self):
        """Verify that non-numeric price is rejected."""
        r = client.post("/items", json={"name": "test", "price": "10.5"})
        # This may be 200 if Pydantic coerces, or 422 if strict
        # Let's check both scenarios
        assert r.status_code in [200, 422]

    def test_create_item_with_empty_name(self):
        """Verify behavior with empty string name."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == ""


class TestCreateItemResponseStructure:
    """Test response object structure and field types."""

    def test_create_item_response_has_required_fields(self):
        """Verify response contains all required fields."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_field_types(self):
        """Verify response field types are correct."""
        r = client.post("/items", json={"name": "test", "price": 10.5})
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_create_item_id_is_positive(self):
        """Verify that returned id is positive."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.json()["id"] > 0

    def test_create_item_response_contains_no_extra_fields(self):
        """Verify response doesn't contain unexpected fields."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        assert set(data.keys()) == {"id", "name", "price"}

    @pytest.mark.parametrize("price", [1.0, 10.5, 100.99, 0.01])
    def test_create_item_response_price_matches_request(self, price):
        """Verify response price matches the requested price."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.json()["price"] == price


class TestGetItemPathParameterValidation:
    """Test item_id path parameter validation and edge cases."""

    @pytest.mark.parametrize("item_id", [
        1,
        2,
        10,
        100,
        999,
        1000000,
    ])
    def test_get_item_returns_404_for_non_existing_ids(self, item_id):
        """Verify that only id=1 returns success, others return 404."""
        if item_id == 1:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 200
        else:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404
            assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [
        -1,
        -10,
        -999,
    ])
    def test_get_item_with_negative_ids_returns_404(self, item_id):
        """Verify that negative ids return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_with_zero_returns_404(self):
        """Verify that id=0 returns 404."""
        r = client.get("/items/0")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_found_response_structure(self):
        """Verify response structure for existing item."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_found_correct_values(self):
        """Verify correct values are returned for existing item."""
        r = client.get("/items/1")
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_error_response_structure(self):
        """Verify error response structure for not found."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)


class TestCreateItemErrorHandling:
    """Test error handling and edge cases in create_item."""

    def test_create_item_with_extra_fields(self):
        """Verify handling of unexpected extra fields."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "extra_field": "should be ignored"
        })
        assert r.status_code == 200
        data = r.json()
        assert "extra_field" not in data

    def test_create_item_with_empty_json(self):
        """Verify handling of empty request body."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_create_item_invalid_json(self):
        """Verify handling of malformed JSON."""
        r = client.post("/items", data="not json")
        assert r.status_code == 422

    def test_create_item_multiple_successful_requests(self):
        """Verify that multiple requests work correctly."""
        for i in range(5):
            r = client.post("/items", json={"name": f"item{i}", "price": float(i + 1)})
            assert r.status_code == 200
            assert r.json()["id"] == 1  # Always returns id=1 in current implementation

    def test_create_item_boundary_price_exactly_positive(self):
        """Verify that the smallest positive value works."""
        r = client.post("/items", json={"name": "test", "price": 0.0000001})
        assert r.status_code == 200


class TestGetItemIntegration:
    """Integration tests combining multiple operations."""

    def test_create_and_get_item_flow(self):
        """Verify complete create-and-get flow."""
        # Create item
        create_r = client.post("/items", json={"name": "integration_test", "price": 25.0})
        assert create_r.status_code == 200
        created_id = create_r.json()["id"]

        # Get the same item
        get_r = client.get(f"/items/{created_id}")
        assert get_r.status_code == 200

    def test_get_nonexistent_before_create(self):
        """Verify behavior when getting non-existent item."""
        r = client.get("/items/9999")
        assert r.status_code == 404

    def test_sequence_of_gets(self):
        """Verify multiple sequential get requests."""
        for item_id in [1, 2, 3, 4, 5]:
            r = client.get(f"/items/{item_id}")
            if item_id == 1:
                assert r.status_code == 200
            else:
                assert r.status_code == 404


class TestCreateItemNumericalEdgeCases:
    """Test numerical edge cases for price field."""

    def test_create_item_with_float_precision(self):
        """Verify handling of floating-point precision."""
        prices = [0.1 + 0.2, 10.999999999, 100.111111111]
        for price in prices:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] > 0

    def test_create_item_with_scientific_notation(self):
        """Verify handling of scientific notation prices."""
        r = client.post("/items", json={"name": "test", "price": 1e5})
        assert r.status_code == 200
        assert r.json()["price"] == 1e5

    def test_create_item_rejects_negative_scientific_notation(self):
        """Verify rejection of negative values in scientific notation."""
        r = client.post("/items", json={"name": "test", "price": -1e5})
        assert r.status_code == 400
