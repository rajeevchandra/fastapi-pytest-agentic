import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemBoundaryValues:
    """Test boundary value conditions for create_item endpoint."""

    @pytest.mark.parametrize("price", [0.001, 0.01, 0.1, 1.0])
    def test_create_item_with_very_small_prices(self, price):
        """Test create_item accepts very small positive prices."""
        response = client.post("/items", json={"name": "item", "price": price})
        assert response.status_code == 200
        assert response.json()["price"] == price

    def test_create_item_exactly_zero(self):
        """Test create_item rejects price exactly 0."""
        response = client.post("/items", json={"name": "test", "price": 0.0})
        assert response.status_code == 400
        assert "price must be > 0" in response.json()["detail"]

    def test_create_item_just_above_zero(self):
        """Test create_item accepts smallest positive price."""
        response = client.post("/items", json={"name": "test", "price": 0.000001})
        assert response.status_code == 200

    @pytest.mark.parametrize("price", [-0.001, -0.1, -1.0, -1000.0])
    def test_create_item_with_slight_negative_prices(self, price):
        """Test create_item rejects even slight negative prices."""
        response = client.post("/items", json={"name": "test", "price": price})
        assert response.status_code == 400


class TestGetItemBoundaryValues:
    """Test boundary value conditions for get_item endpoint."""

    def test_get_item_id_zero(self):
        """Test get_item with item_id=0 returns 404."""
        response = client.get("/items/0")
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"

    def test_get_item_id_negative_one(self):
        """Test get_item with item_id=-1 returns 404."""
        response = client.get("/items/-1")
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [-999, -1000, -1])
    def test_get_item_negative_ids(self, item_id):
        """Test get_item returns 404 for all negative item_ids."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404

    @pytest.mark.parametrize("item_id", [2, 3, 100, 1000, 999999])
    def test_get_item_ids_greater_than_one(self, item_id):
        """Test get_item returns 404 for all item_ids != 1."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404


class TestGetItemOnlyValidId:
    """Test that only item_id=1 is valid."""

    def test_get_item_id_one_returns_success(self):
        """Test get_item with item_id=1 returns 200."""
        response = client.get("/items/1")
        assert response.status_code == 200

    @pytest.mark.parametrize("item_id", range(2, 10))
    def test_get_item_ids_2_through_9_fail(self, item_id):
        """Test get_item with item_ids 2-9 all return 404."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404


class TestCreateAndRetrieveSequence:
    """Test integration scenarios combining create and get operations."""

    def test_create_then_get_returns_one(self):
        """Test that after create_item, get_item always returns item 1."""
        create_response = client.post("/items", json={"name": "new_item", "price": 25.0})
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]
        
        get_response = client.get(f"/items/{created_id}")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == 1

    def test_multiple_creates_all_return_id_one(self):
        """Test multiple creates all return the same item id=1."""
        response1 = client.post("/items", json={"name": "item1", "price": 5.0})
        response2 = client.post("/items", json={"name": "item2", "price": 10.0})
        response3 = client.post("/items", json={"name": "item3", "price": 15.0})
        
        assert response1.json()["id"] == 1
        assert response2.json()["id"] == 1
        assert response3.json()["id"] == 1


class TestPriceValidationConsistency:
    """Test price validation is applied consistently."""

    @pytest.mark.parametrize("price,should_succeed", [
        (0.001, True),
        (1.0, True),
        (100.5, True),
        (0, False),
        (-0.001, False),
        (-1, False),
    ])
    def test_price_validation_consistency(self, price, should_succeed):
        """Test price validation behaves consistently across calls."""
        response = client.post("/items", json={"name": "test", "price": price})
        if should_succeed:
            assert response.status_code == 200
            assert response.json()["price"] == price
        else:
            assert response.status_code == 400
            assert "price must be > 0" in response.json()["detail"]


class TestDataPersistence:
    """Test data handling and persistence patterns."""

    def test_get_item_always_returns_same_data(self):
        """Test get_item(1) always returns consistent data."""
        response1 = client.get("/items/1")
        response2 = client.get("/items/1")
        
        data1 = response1.json()
        data2 = response2.json()
        
        assert data1["id"] == data2["id"]
        assert data1["name"] == data2["name"]
        assert data1["price"] == data2["price"]

    def test_created_items_with_different_names_both_return_id_one(self):
        """Test that all creates return the same item regardless of input."""
        response1 = client.post("/items", json={"name": "product_a", "price": 5.0})
        response2 = client.post("/items", json={"name": "product_b", "price": 10.0})
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Both should return id 1, even though they have different names
        assert data1["id"] == 1
        assert data2["id"] == 1
        assert data1["name"] == "product_a"
        assert data2["name"] == "product_b"


class TestResponseDataTypes:
    """Test that response data types are consistent and correct."""

    def test_create_item_price_preserves_type(self):
        """Test create_item preserves float type for price."""
        response = client.post("/items", json={"name": "test", "price": 10.5})
        data = response.json()
        # Price should be returned as-is (float)
        assert isinstance(data["price"], (int, float))
        assert data["price"] == 10.5

    def test_get_item_price_is_float(self):
        """Test get_item returns price as float."""
        response = client.get("/items/1")
        data = response.json()
        assert isinstance(data["price"], (int, float))
        assert data["price"] == 10.0

    def test_create_item_returns_integer_id(self):
        """Test create_item returns id as integer."""
        response = client.post("/items", json={"name": "test", "price": 5.0})
        data = response.json()
        assert isinstance(data["id"], int)

    def test_get_item_returns_integer_id(self):
        """Test get_item returns id as integer."""
        response = client.get("/items/1")
        data = response.json()
        assert isinstance(data["id"], int)


class TestErrorConditionRecovery:
    """Test recovery from error conditions."""

    def test_create_with_error_then_success(self):
        """Test successful create after failed create."""
        # First call with invalid price
        error_response = client.post("/items", json={"name": "bad", "price": 0})
        assert error_response.status_code == 400
        
        # Second call with valid price should succeed
        success_response = client.post("/items", json={"name": "good", "price": 10.0})
        assert success_response.status_code == 200
        assert success_response.json()["price"] == 10.0

    def test_get_nonexistent_then_get_existing(self):
        """Test successful get after failed get."""
        # Get non-existent item
        not_found_response = client.get("/items/2")
        assert not_found_response.status_code == 404
        
        # Get existing item should still work
        found_response = client.get("/items/1")
        assert found_response.status_code == 200
        assert found_response.json()["id"] == 1


class TestNameFieldPreservation:
    """Test that name field is properly preserved in responses."""

    @pytest.mark.parametrize("name", [
        "simple",
        "with spaces",
        "with-dashes",
        "with_underscores",
        "123numeric",
        "MixedCase",
    ])
    def test_create_preserves_name_exactly(self, name):
        """Test create_item returns the exact name provided."""
        response = client.post("/items", json={"name": name, "price": 5.0})
        assert response.json()["name"] == name

    def test_create_case_sensitivity(self):
        """Test create_item is case-sensitive for names."""
        response1 = client.post("/items", json={"name": "Test", "price": 5.0})
        response2 = client.post("/items", json={"name": "test", "price": 5.0})
        
        assert response1.json()["name"] == "Test"
        assert response2.json()["name"] == "test"
        assert response1.json()["name"] != response2.json()["name"]


class TestComplexIntegrationScenarios:
    """Test complex scenarios involving multiple operations."""

    def test_multiple_failures_and_successes(self):
        """Test handling multiple error cases followed by success."""
        # Multiple errors
        client.post("/items", json={"name": "a", "price": 0})
        client.post("/items", json={"name": "b", "price": -5})
        client.post("/items", json={"name": "c", "price": -100})
        
        # Success
        response = client.post("/items", json={"name": "d", "price": 20.0})
        assert response.status_code == 200
        assert response.json()["name"] == "d"
        
        # Verify item 1 still works
        get_response = client.get("/items/1")
        assert get_response.status_code == 200

    def test_endpoint_independence(self):
        """Test that endpoints work independently."""
        # Create succeeds
        create_response = client.post("/items", json={"name": "test", "price": 5.0})
        assert create_response.status_code == 200
        
        # Get exists
        get_response = client.get("/items/1")
        assert get_response.status_code == 200
        
        # Health is independent
        health_response = client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "ok"
