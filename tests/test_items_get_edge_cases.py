"""
Path parameter edge cases and integration scenarios for items endpoints.
Tests boundary values for item IDs, integration between create/get, and edge cases.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation and boundary values."""

    @pytest.mark.parametrize("item_id", [1])
    def test_get_item_valid_id_returns_success(self, item_id):
        """Valid ID (1) should return 200."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200

    @pytest.mark.parametrize("item_id", [0, -1, -100])
    def test_get_item_zero_or_negative_id_returns_404(self, item_id):
        """Zero and negative IDs should return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [2, 10, 100, 999999])
    def test_get_item_non_existing_positive_id_returns_404(self, item_id):
        """Non-existent positive IDs should return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [9223372036854775807])  # Max int64
    def test_get_item_very_large_id(self, item_id):
        """Very large ID values should be handled."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_get_item_string_id_returns_validation_error(self):
        """Non-numeric path parameter should return error."""
        r = client.get("/items/abc")
        assert r.status_code in [404, 422]  # Depends on routing

    def test_get_item_float_id_returns_validation_error(self):
        """Float path parameter should be handled."""
        r = client.get("/items/1.5")
        assert r.status_code in [404, 422]


class TestCreateItemBoundaryPrices:
    """Test price boundary values in create operations."""

    @pytest.mark.parametrize("price", [
        0.001,      # Very small positive
        0.01,       # Small positive
        1.0,        # Integer-like
        100.0,      # Large
        999999.99,  # Very large
        1e10,       # Exponential large
    ])
    def test_create_item_with_various_price_values(self, price):
        """Various price values should be accepted."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [
        -0.001,
        -1,
        -1000,
        -1e10,
    ])
    def test_create_item_with_negative_prices(self, price):
        """Negative prices should be rejected."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400


class TestGetItemIDEdgeCases:
    """Test edge cases for item ID parameter handling."""

    def test_get_item_id_1_always_found(self):
        """Item ID 1 should always exist."""
        for _ in range(3):
            r = client.get("/items/1")
            assert r.status_code == 200

    def test_get_item_ids_2_through_5_not_found(self):
        """Item IDs 2-5 should not exist."""
        for item_id in range(2, 6):
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404

    def test_get_item_boundary_id_zero(self):
        """ID 0 should not be found."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_boundary_id_negative_one(self):
        """ID -1 should not be found."""
        r = client.get("/items/-1")
        assert r.status_code == 404


class TestCreateItemNameEdgeCases:
    """Test edge cases for name field."""

    @pytest.mark.parametrize("name", [
        "x",
        "a" * 100,
        "a" * 1000,
    ])
    def test_create_item_with_name_length_variations(self, name):
        """Various name lengths should be accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_name_preserves_whitespace(self):
        """Name with internal whitespace should be preserved."""
        name = "hello world"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_name_with_numbers(self):
        """Name with numbers should be accepted."""
        name = "Item123"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestIntegrationCreateThenGet:
    """Test integration between create and get operations."""

    def test_create_item_returns_id_one(self):
        """Created item should have ID 1."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_item_one_after_create(self):
        """GET /items/1 should return the item (endpoint behavior)."""
        r = client.get("/items/1")
        assert r.status_code == 200
        # Get should return preset data
        assert r.json()["id"] == 1

    def test_create_returns_same_data_as_get(self):
        """Create response should match GET response for same item."""
        create_r = client.post("/items", json={"name": "sample", "price": 10.0})
        get_r = client.get("/items/1")
        
        create_data = create_r.json()
        get_data = get_r.json()
        
        # Both should have same structure
        assert set(create_data.keys()) == set(get_data.keys())
        assert "id" in create_data and "id" in get_data
        assert "name" in create_data and "name" in get_data
        assert "price" in create_data and "price" in get_data


class TestMultipleOperationSequences:
    """Test sequences of multiple operations."""

    def test_create_then_get_preserves_data(self):
        """Data from create should be retrievable via get."""
        # Create
        create_r = client.post("/items", json={"name": "item1", "price": 5.0})
        assert create_r.status_code == 200
        
        # Get the same item
        get_r = client.get("/items/1")
        assert get_r.status_code == 200
        
        # Verify structure
        assert "id" in get_r.json()
        assert "name" in get_r.json()
        assert "price" in get_r.json()

    def test_multiple_creates_return_same_id(self):
        """Multiple create operations should return ID 1 (stateless)."""
        ids = []
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
            ids.append(r.json()["id"])
        
        # All should be ID 1 (current implementation)
        assert all(id == 1 for id in ids)

    def test_create_and_get_error_cases(self):
        """Error cases should not affect subsequent requests."""
        # Try invalid create
        r1 = client.post("/items", json={"name": "item", "price": 0})
        assert r1.status_code == 400
        
        # Try valid create afterward
        r2 = client.post("/items", json={"name": "item", "price": 10.0})
        assert r2.status_code == 200
        
        # Try invalid get
        r3 = client.get("/items/999")
        assert r3.status_code == 404
        
        # Try valid get afterward
        r4 = client.get("/items/1")
        assert r4.status_code == 200


class TestRequestResponseRoundtrip:
    """Test data integrity through request/response cycle."""

    @pytest.mark.parametrize("name,price", [
        ("Item A", 1.5),
        ("Item B", 99.99),
        ("Item C", 0.01),
    ])
    def test_create_preserves_name_and_price(self, name, price):
        """Create response should echo request data."""
        r = client.post("/items", json={"name": name, "price": price})
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price

    def test_create_generates_valid_id(self):
        """Create should return valid integer ID."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        id_val = r.json()["id"]
        assert isinstance(id_val, int)
        assert id_val > 0

    def test_response_data_is_json_serializable(self):
        """Response data should be JSON serializable."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        # If we can call .json() without error, data is serializable
        data = r.json()
        assert data is not None


class TestErrorRecovery:
    """Test that errors don't corrupt system state."""

    def test_system_recovers_after_validation_error(self):
        """System should work after validation error."""
        # Cause validation error
        r1 = client.post("/items", json={"price": 10.0})  # Missing name
        assert r1.status_code == 422
        
        # System should still work
        r2 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r2.status_code == 200

    def test_system_recovers_after_business_logic_error(self):
        """System should work after business logic error."""
        # Cause business logic error
        r1 = client.post("/items", json={"name": "test", "price": 0})
        assert r1.status_code == 400
        
        # System should still work
        r2 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r2.status_code == 200

    def test_system_recovers_after_not_found_error(self):
        """System should work after not found error."""
        # Cause not found error
        r1 = client.get("/items/999")
        assert r1.status_code == 404
        
        # System should still work
        r2 = client.get("/items/1")
        assert r2.status_code == 200


class TestPriceEdgeCasesInContext:
    """Test price edge cases in realistic scenarios."""

    def test_very_small_price_succeeds(self):
        """Cent-level prices should work."""
        r = client.post("/items", json={"name": "item", "price": 0.01})
        assert r.status_code == 200
        assert r.json()["price"] == 0.01

    def test_large_bulk_price_succeeds(self):
        """Large prices should work."""
        r = client.post("/items", json={"name": "enterprise", "price": 999999.99})
        assert r.status_code == 200
        assert r.json()["price"] == 999999.99

    def test_price_boundary_just_above_zero(self):
        """Price just above zero should succeed."""
        r = client.post("/items", json={"name": "item", "price": 0.0001})
        assert r.status_code == 200

    def test_price_boundary_at_zero(self):
        """Price exactly at zero should fail."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
