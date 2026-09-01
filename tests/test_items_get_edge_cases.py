"""
Test suite for edge cases and integration scenarios on the /items endpoints.
Tests cover path parameter edge cases, integration scenarios, and boundary conditions.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Tests for path parameter validation in GET /items/{item_id}."""

    @pytest.mark.parametrize("item_id", [1])
    def test_get_item_valid_id_returns_data(self, item_id):
        """Valid item ID should return item data."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200
        assert r.json()["id"] == item_id

    @pytest.mark.parametrize("item_id", [2, 3, 10, 100, 999, 99999])
    def test_get_item_different_valid_ids_not_found(self, item_id):
        """Non-existent item IDs should return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [-1, -100, -999])
    def test_get_item_negative_ids_not_found(self, item_id):
        """Negative item IDs should return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_get_item_zero_id_not_found(self):
        """Item ID 0 should return 404."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_large_id_not_found(self):
        """Very large item ID should return 404."""
        r = client.get("/items/999999999")
        assert r.status_code == 404

    def test_get_item_id_one_returns_fixed_data(self):
        """Item ID 1 should always return consistent data."""
        r = client.get("/items/1")
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0


class TestCreateItemWithVariousPrices:
    """Tests for price handling across different scales and values."""

    @pytest.mark.parametrize("price", [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0])
    def test_create_item_various_price_scales(self, price):
        """Different price scales should be handled correctly."""
        r = client.post("/items", json={"name": f"item_{price}", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [0.001, 0.0001, 1.5, 99.99, 999.99])
    def test_create_item_decimal_prices(self, price):
        """Decimal prices should work correctly."""
        r = client.post("/items", json={"name": "decimal", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_create_item_price_boundary_just_above_zero(self):
        """Price just above zero should be accepted."""
        r = client.post("/items", json={"name": "min_price", "price": 0.0001})
        assert r.status_code == 200
        assert r.json()["price"] == 0.0001

    def test_create_item_price_exact_zero_rejected(self):
        """Exact zero price should be rejected."""
        r = client.post("/items", json={"name": "zero", "price": 0.0})
        assert r.status_code == 400

    def test_create_item_price_just_below_zero_rejected(self):
        """Price just below zero should be rejected."""
        r = client.post("/items", json={"name": "negative", "price": -0.0001})
        assert r.status_code == 400

    def test_create_item_very_large_price(self):
        """Very large prices should be accepted."""
        r = client.post("/items", json={"name": "expensive", "price": 999999.99})
        assert r.status_code == 200
        assert r.json()["price"] == 999999.99


class TestCreateItemWithVariousNames:
    """Tests for name field handling across different content."""

    @pytest.mark.parametrize("name", [
        "a",
        "ab",
        "a" * 50,
        "a" * 100,
        "name with spaces",
        "name_with_underscore",
        "name-with-dash",
    ])
    def test_create_item_various_name_lengths(self, name):
        """Various name lengths should be accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_name_single_char(self):
        """Single character name should work."""
        r = client.post("/items", json={"name": "x", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "x"

    def test_create_item_name_very_long(self):
        """Very long name should work."""
        long_name = "x" * 1000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_create_item_name_with_numbers(self):
        """Name with numbers should work."""
        r = client.post("/items", json={"name": "item123abc", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "item123abc"

    def test_create_item_name_with_special_chars(self):
        """Name with special characters should work."""
        r = client.post("/items", json={"name": "item@!#$%^&*()", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "item@!#$%^&*()"


class TestMultipleCreateAndRetrieve:
    """Tests for multiple create operations and interactions."""

    def test_create_two_different_items_sequentially(self):
        """Creating two items should both succeed."""
        r1 = client.post("/items", json={"name": "first", "price": 10.0})
        r2 = client.post("/items", json={"name": "second", "price": 20.0})
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["name"] == "first"
        assert r2.json()["name"] == "second"

    def test_create_then_retrieve_same_item(self):
        """Create item then retrieve by ID should return same data."""
        create_r = client.post("/items", json={"name": "test_item", "price": 15.5})
        assert create_r.status_code == 200
        created_data = create_r.json()
        
        get_r = client.get(f"/items/{created_data['id']}")
        assert get_r.status_code == 200
        retrieved_data = get_r.json()
        assert retrieved_data["name"] == "test_item"
        assert retrieved_data["price"] == 15.5

    def test_create_item_and_verify_response_id(self):
        """Created item should have valid ID."""
        r = client.post("/items", json={"name": "id_test", "price": 5.0})
        data = r.json()
        assert data["id"] > 0
        assert isinstance(data["id"], int)

    def test_multiple_creates_different_names(self):
        """Multiple creates with different names should all succeed."""
        names = ["apple", "banana", "cherry", "date", "elderberry"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name


class TestErrorConditionCombinations:
    """Tests for combinations of error conditions."""

    def test_create_item_negative_price_and_missing_name(self):
        """Missing field takes precedence over price validation."""
        r = client.post("/items", json={"price": -1})
        assert r.status_code == 422

    def test_create_item_invalid_price_type_and_missing_name(self):
        """Multiple validation errors."""
        r = client.post("/items", json={"price": "invalid"})
        assert r.status_code == 422

    def test_get_item_then_create_then_get_not_found(self):
        """Get non-existent, create, then get non-existent again."""
        r1 = client.get("/items/999")
        assert r1.status_code == 404
        
        r2 = client.post("/items", json={"name": "new", "price": 5.0})
        assert r2.status_code == 200
        
        r3 = client.get("/items/999")
        assert r3.status_code == 404

    def test_create_with_exact_boundary_price(self):
        """Price at exact boundaries."""
        # Just above zero should work
        r1 = client.post("/items", json={"name": "min", "price": 0.0000001})
        assert r1.status_code == 200
        
        # Exactly zero should fail
        r2 = client.post("/items", json={"name": "zero", "price": 0.0})
        assert r2.status_code == 400


class TestResponseDataAccuracy:
    """Tests to verify response data accuracy and consistency."""

    def test_create_item_response_matches_request(self):
        """Response should contain data from request."""
        request_data = {"name": "accuracy_test", "price": 42.5}
        r = client.post("/items", json=request_data)
        response = r.json()
        assert response["name"] == request_data["name"]
        assert response["price"] == request_data["price"]

    def test_get_item_response_accuracy(self):
        """GET /items/1 should return known correct data."""
        r = client.get("/items/1")
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_create_item_preserves_numeric_precision(self):
        """Numeric precision should be preserved."""
        r = client.post("/items", json={"name": "precision", "price": 99.99})
        assert r.json()["price"] == 99.99

    def test_create_item_preserves_string_exactly(self):
        """String names should be preserved exactly."""
        test_name = "special name with  spaces"
        r = client.post("/items", json={"name": test_name, "price": 10.0})
        assert r.json()["name"] == test_name


class TestErrorDetailMessages:
    """Tests for error detail message accuracy."""

    def test_price_error_has_exact_message(self):
        """Price validation error should have exact message."""
        r = client.post("/items", json={"name": "test", "price": -5})
        assert r.json()["detail"] == "price must be > 0"

    def test_not_found_error_has_exact_message(self):
        """404 error should have exact message."""
        r = client.get("/items/2")
        assert r.json()["detail"] == "not found"

    def test_missing_field_error_contains_field_info(self):
        """Validation error for missing fields should include field info."""
        r = client.post("/items", json={"name": "test"})
        data = r.json()
        assert "detail" in data
        # Detail should provide information about the error
        assert data["detail"] is not None

    def test_zero_price_error_has_correct_message(self):
        """Zero price validation should have same message as negative."""
        r1 = client.post("/items", json={"name": "test", "price": 0})
        r2 = client.post("/items", json={"name": "test", "price": -1})
        assert r1.json()["detail"] == r2.json()["detail"]


class TestEdgeCaseIntegration:
    """Integration tests for edge case combinations."""

    def test_create_item_with_min_valid_price_and_short_name(self):
        """Minimum valid price with short name."""
        r = client.post("/items", json={"name": "x", "price": 0.01})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "x"
        assert data["price"] == 0.01

    def test_create_item_with_max_price_and_long_name(self):
        """Maximum price with long name."""
        long_name = "a" * 500
        r = client.post("/items", json={"name": long_name, "price": 999999.99})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == long_name
        assert data["price"] == 999999.99

    def test_get_boundary_item_ids(self):
        """Test getting items at ID boundaries."""
        r1 = client.get("/items/1")
        assert r1.status_code == 200
        
        r2 = client.get("/items/2")
        assert r2.status_code == 404
        
        r3 = client.get("/items/0")
        assert r3.status_code == 404

    def test_alternating_create_and_get_failures(self):
        """Alternating create success and get failure."""
        r1 = client.post("/items", json={"name": "item1", "price": 1.0})
        assert r1.status_code == 200
        
        r2 = client.get("/items/999")
        assert r2.status_code == 404
        
        r3 = client.post("/items", json={"name": "item2", "price": 2.0})
        assert r3.status_code == 200
        
        r4 = client.get("/items/1")
        assert r4.status_code == 200
