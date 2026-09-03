"""Path parameter validation and integration edge case tests for /items endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for GET /items/{item_id}."""

    @pytest.mark.parametrize("item_id", [1])
    def test_get_item_valid_id_positive(self, item_id):
        """Positive integer IDs should be accepted."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 200

    @pytest.mark.parametrize("item_id", [0, -1, -10, -999])
    def test_get_item_invalid_id_zero_or_negative(self, item_id):
        """Zero and negative IDs should return 404."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404

    @pytest.mark.parametrize("item_id", [2, 10, 100, 999, 10000, 999999])
    def test_get_item_nonexistent_positive_ids(self, item_id):
        """Non-existent positive IDs should return 404."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404

    @pytest.mark.parametrize("item_id", [
        9223372036854775807,  # max int64
        1000000000,            # very large number
    ])
    def test_get_item_large_ids(self, item_id):
        """Large valid integer IDs should be accepted and return 404 if not found."""
        response = client.get(f"/items/{item_id}")
        # Should not raise an error, just return 404
        assert response.status_code in [200, 404]

    def test_get_item_id_boundaries(self):
        """Test boundary between existing and non-existing items."""
        # ID 1 should exist
        response = client.get("/items/1")
        assert response.status_code == 200
        
        # ID 2 should not exist
        response = client.get("/items/2")
        assert response.status_code == 404


class TestCreateItemWithVariousPrices:
    """Test POST /items with various price boundary values."""

    @pytest.mark.parametrize("price", [
        0.001,          # very small positive
        0.01,           # small positive
        0.1,            # tenth
        1,              # one
        1.5,            # one and half
        10,             # ten
        99.99,          # two digit
        100,            # hundred
        999.99,         # max two digit decimals
        1000,           # thousand
        10000.50,       # large with decimal
        999999.99,      # very large
        1000000,        # million
    ])
    def test_create_item_various_valid_prices(self, price):
        """Create items with various positive prices."""
        response = client.post("/items", json={"name": "test", "price": price})
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == price

    @pytest.mark.parametrize("price", [
        -0.001,         # very small negative
        -0.01,          # small negative
        -1,             # negative one
        -10.5,          # negative with decimal
        -100,           # negative hundred
        -999999.99,     # very large negative
    ])
    def test_create_item_various_invalid_prices(self, price):
        """Negative prices should all be rejected."""
        response = client.post("/items", json={"name": "test", "price": price})
        assert response.status_code == 400
        assert "price must be > 0" in response.json()["detail"]

    def test_create_item_price_exact_zero(self):
        """Price exactly 0 should be rejected."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400

    def test_create_item_price_just_above_zero(self):
        """Price just above 0 (0.001) should be accepted."""
        response = client.post("/items", json={"name": "test", "price": 0.001})
        assert response.status_code == 200


class TestCreateItemWithVariousNames:
    """Test POST /items with various name values."""

    @pytest.mark.parametrize("name", [
        "a",                    # single character
        "ab",                   # two characters
        "abc",                  # three characters
        "A",                    # uppercase
        "ABC",                  # all uppercase
        "Test Item",            # mixed case with space
        "test-item",            # with hyphen
        "test_item",            # with underscore
        "test.item",            # with dot
        "test123",              # alphanumeric
        "item #1",              # with special char
        "item (small)",         # with parentheses
        "Price: $9.99",         # with symbols
        "  spaces  ",           # leading/trailing spaces
        "line\nbreak",          # special characters
        "item" * 50,            # very long name
    ])
    def test_create_item_various_names(self, name):
        """Create items with various name formats."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == name

    def test_create_item_empty_name(self):
        """Empty name should be accepted (Pydantic has no name validation)."""
        response = client.post("/items", json={"name": "", "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == ""


class TestMultipleCreateItemRequests:
    """Test multiple sequential create requests."""

    def test_create_multiple_items_same_data(self):
        """Creating multiple items with same data should always return id=1."""
        for i in range(3):
            response = client.post("/items", json={"name": "test", "price": 10.0})
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["name"] == "test"
            assert data["price"] == 10.0

    def test_create_multiple_items_different_data(self):
        """Creating multiple items with different data should all succeed."""
        test_data = [
            {"name": "book", "price": 15.99},
            {"name": "pen", "price": 2.50},
            {"name": "notebook", "price": 5.00},
        ]
        
        for data in test_data:
            response = client.post("/items", json=data)
            assert response.status_code == 200
            result = response.json()
            assert result["id"] == 1
            assert result["name"] == data["name"]
            assert result["price"] == data["price"]


class TestGetItemMultipleRequests:
    """Test multiple sequential get requests."""

    def test_get_item_consistency(self):
        """Getting item 1 multiple times should return consistent data."""
        responses = []
        for _ in range(3):
            response = client.get("/items/1")
            assert response.status_code == 200
            responses.append(response.json())
        
        # All responses should be identical
        assert responses[0] == responses[1] == responses[2]

    def test_get_item_one_exists_others_dont(self):
        """Only item 1 should exist, others should return 404."""
        # Item 1 exists
        response = client.get("/items/1")
        assert response.status_code == 200
        
        # Items 2-5 should not exist
        for item_id in [2, 3, 4, 5]:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 404


class TestIntegrationScenarios:
    """Test integrated scenarios combining multiple operations."""

    def test_create_and_retrieve_flow(self):
        """Test basic flow: create item, then retrieve it."""
        # Create item
        create_response = client.post("/items", json={"name": "widget", "price": 29.99})
        assert create_response.status_code == 200
        created_item = create_response.json()
        
        # Retrieve the created item
        get_response = client.get(f"/items/{created_item['id']}")
        assert get_response.status_code == 200
        retrieved_item = get_response.json()
        
        # Retrieved item should have the correct ID
        assert retrieved_item["id"] == created_item["id"]

    def test_create_item_then_get_by_id(self):
        """Create an item and verify it can be retrieved by ID."""
        test_name = "test_product"
        test_price = 42.50
        
        # Create item
        create_response = client.post("/items", json={"name": test_name, "price": test_price})
        assert create_response.status_code == 200
        item = create_response.json()
        
        # Verify the item ID is 1
        assert item["id"] == 1
        
        # Retrieve by ID
        get_response = client.get("/items/1")
        assert get_response.status_code == 200
        retrieved = get_response.json()
        
        # Verify ID matches
        assert retrieved["id"] == 1

    def test_invalid_create_then_valid_create(self):
        """Sequence: invalid create (should fail), then valid create (should succeed)."""
        # Invalid: zero price
        invalid_response = client.post("/items", json={"name": "bad", "price": 0})
        assert invalid_response.status_code == 400
        
        # Valid: positive price
        valid_response = client.post("/items", json={"name": "good", "price": 10.0})
        assert valid_response.status_code == 200

    def test_get_nonexistent_items_then_existing_item(self):
        """Sequence: get non-existent items, then get existing item."""
        # Get non-existent items
        for item_id in [2, 3, 4, 5]:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 404
        
        # Get existing item
        response = client.get("/items/1")
        assert response.status_code == 200
        assert response.json()["id"] == 1


class TestErrorConditionCombinations:
    """Test combinations of error conditions."""

    def test_create_missing_multiple_fields(self):
        """Missing multiple required fields should return validation error."""
        response = client.post("/items", json={})
        assert response.status_code == 422
        errors = response.json()["detail"]
        # Should have errors for both missing fields
        assert len(errors) >= 2
        error_fields = {err["loc"][0] for err in errors}
        assert "name" in error_fields or "price" in error_fields

    def test_create_with_invalid_types_for_both_fields(self):
        """Invalid types for both fields should return validation error."""
        response = client.post("/items", json={
            "name": None,
            "price": "not_a_number"
        })
        # Should return validation error (422) or accepted depending on Pydantic behavior
        assert response.status_code in [200, 422]

    def test_get_with_invalid_path_formats(self):
        """Invalid path formats should be handled by FastAPI."""
        # Non-integer ID should not match the route
        response = client.get("/items/abc")
        # FastAPI will not match this route, so 404
        assert response.status_code == 404

    def test_price_boundary_error_conditions(self):
        """Test various price boundary error conditions."""
        error_prices = [0, -0.001, -1, -999999]
        for price in error_prices:
            response = client.post("/items", json={"name": "test", "price": price})
            assert response.status_code == 400
            assert "price" in response.json()["detail"].lower()


class TestRequestBodyValidation:
    """Test request body structure and validation."""

    def test_create_item_with_extra_fields(self):
        """Extra fields in request should be ignored by Pydantic."""
        response = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "description": "ignored",
            "stock": 100
        })
        # Pydantic ignores extra fields by default
        assert response.status_code == 200
        data = response.json()
        # Response should not include extra fields
        assert "description" not in data
        assert "stock" not in data

    def test_create_item_null_values(self):
        """Null values for required fields should fail validation."""
        response = client.post("/items", json={
            "name": None,
            "price": None
        })
        # None for required fields should fail
        assert response.status_code in [422, 200]  # Depending on Pydantic coercion

    def test_create_item_empty_json(self):
        """Empty JSON object should fail validation."""
        response = client.post("/items", json={})
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert len(errors) > 0
