"""
Edge Cases and Integration Tests for API endpoints.
Tests for boundary values, integration scenarios, and complex interactions.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemIdBoundaryValues:
    """Test /items/{item_id} GET with boundary value item IDs."""

    @pytest.mark.parametrize("item_id", [
        2, 3, 10, 100, 1000, 999999, 2147483647  # max 32-bit int
    ])
    def test_get_item_not_found_various_ids(self, item_id):
        """Test not found for various item IDs."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [0, -1, -10, -100, -999])
    def test_get_item_negative_ids(self, item_id):
        """Test not found for negative item IDs."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_zero_id(self):
        """Test zero item ID returns not found."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_very_large_id(self):
        """Test very large item ID returns not found."""
        r = client.get(f"/items/{10**20}")
        assert r.status_code == 404

    def test_get_item_id_one_only_found(self):
        """Test only item_id=1 is found."""
        for item_id in [0, 1, 2, -1, 100]:
            r = client.get(f"/items/{item_id}")
            if item_id == 1:
                assert r.status_code == 200
            else:
                assert r.status_code == 404


class TestCreateItemPriceBoundaries:
    """Test /items POST price with boundary conditions."""

    @pytest.mark.parametrize("price", [
        0.001,
        0.0001,
        0.00001,
        1e-6,
        1e-10,
    ])
    def test_create_item_very_small_positive_prices(self, price):
        """Test create_item accepts very small positive prices."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [
        1e6,
        1e9,
        1e12,
        999999999999.99,
    ])
    def test_create_item_very_large_prices(self, price):
        """Test create_item accepts very large prices."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [
        -0.000001,
        -1e-10,
        -0.0001,
    ])
    def test_create_item_very_small_negative_prices(self, price):
        """Test create_item rejects very small negative prices."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [
        -1e6,
        -1e12,
        -999999999999.99,
    ])
    def test_create_item_very_large_negative_prices(self, price):
        """Test create_item rejects very large negative prices."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"


class TestCreateItemNameBoundaries:
    """Test /items POST name with boundary conditions."""

    def test_create_item_single_char_name(self):
        """Test create_item accepts single character name."""
        r = client.post("/items", json={"name": "x", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "x"

    def test_create_item_whitespace_only_name(self):
        """Test create_item accepts whitespace-only name."""
        names = [" ", "   ", "\t", "\n", "  \t  \n  "]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name

    def test_create_item_numeric_string_name(self):
        """Test create_item accepts numeric string as name."""
        r = client.post("/items", json={"name": "12345", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "12345"

    def test_create_item_repeated_char_name(self):
        """Test create_item accepts repeated character name."""
        r = client.post("/items", json={"name": "aaaaaaaaaa", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "aaaaaaaaaa"


class TestIntegrationCreateAndGet:
    """Test integration between create and get endpoints."""

    def test_create_item_then_get_item(self):
        """Test create an item then retrieve it."""
        create_r = client.post("/items", json={"name": "book", "price": 12.5})
        assert create_r.status_code == 200
        created_data = create_r.json()
        
        get_r = client.get(f"/items/{created_data['id']}")
        assert get_r.status_code == 200
        get_data = get_r.json()
        
        # get_item returns fixed data, not created data
        assert get_data["id"] == 1
        assert get_data["name"] == "sample"
        assert get_data["price"] == 10.0

    def test_create_multiple_items_all_return_id_1(self):
        """Test multiple creates all return id=1."""
        for i in range(5):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_get_after_successful_create(self):
        """Test get_item(1) works after creating."""
        client.post("/items", json={"name": "new", "price": 20.0})
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_create_after_get(self):
        """Test create after get."""
        client.get("/items/1")
        r = client.post("/items", json={"name": "after", "price": 5.0})
        assert r.status_code == 200
        assert r.json()["id"] == 1


class TestErrorRecovery:
    """Test API behavior after errors."""

    def test_health_after_create_error(self):
        """Test health endpoint works after create error."""
        client.post("/items", json={"name": "test", "price": 0})  # error
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_health_after_get_error(self):
        """Test health endpoint works after get error."""
        client.get("/items/999")  # not found
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_create_after_validation_error(self):
        """Test create works after validation error."""
        client.post("/items", json={"name": "test"})  # missing price
        r = client.post("/items", json={"name": "valid", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_after_previous_error(self):
        """Test get works after various errors."""
        client.post("/items", json={"name": "test", "price": -1})  # error
        client.post("/items", json={"name": "test"})  # error
        r = client.get("/items/1")
        assert r.status_code == 200


class TestSequentialOperations:
    """Test sequential API operations."""

    def test_multiple_creates_in_sequence(self):
        """Test multiple creates in sequence."""
        for i in range(10):
            r = client.post("/items", json={"name": f"item{i}", "price": float(i + 1)})
            assert r.status_code == 200
            data = r.json()
            assert data["id"] == 1
            assert data["name"] == f"item{i}"
            assert data["price"] == float(i + 1)

    def test_multiple_gets_in_sequence(self):
        """Test multiple gets in sequence."""
        for _ in range(10):
            r = client.get("/items/1")
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_interleaved_create_and_get(self):
        """Test interleaved creates and gets."""
        for i in range(5):
            create_r = client.post("/items", json={"name": f"item{i}", "price": float(i)})
            assert create_r.status_code == 200
            
            get_r = client.get("/items/1")
            assert get_r.status_code == 200

    def test_error_then_success_sequence(self):
        """Test error followed by success."""
        error_r = client.post("/items", json={"name": "bad", "price": 0})
        assert error_r.status_code == 400
        
        success_r = client.post("/items", json={"name": "good", "price": 10.0})
        assert success_r.status_code == 200


class TestEndpointSpecificBehavior:
    """Test specific endpoint behaviors."""

    def test_create_item_always_creates(self):
        """Test create_item always succeeds with valid input."""
        for i in range(10):
            r = client.post("/items", json={"name": f"test{i}", "price": 10.0 + i * 0.1})
            assert r.status_code == 200

    def test_get_item_deterministic(self):
        """Test get_item(1) is deterministic."""
        results = []
        for _ in range(5):
            r = client.get("/items/1")
            assert r.status_code == 200
            results.append(r.json())
        
        # All results should be identical
        for result in results[1:]:
            assert result == results[0]

    def test_get_item_immutable(self):
        """Test get_item(1) returns fixed data regardless of creates."""
        first_get = client.get("/items/1").json()
        
        client.post("/items", json={"name": "new", "price": 99.99})
        
        second_get = client.get("/items/1").json()
        
        assert first_get == second_get


class TestDataConsistency:
    """Test data consistency across operations."""

    def test_create_response_matches_request(self):
        """Test create response matches request data."""
        test_cases = [
            {"name": "item1", "price": 10.0},
            {"name": "café", "price": 5.5},
            {"name": "🎁", "price": 1.0},
        ]
        
        for case in test_cases:
            r = client.post("/items", json=case)
            assert r.status_code == 200
            data = r.json()
            assert data["name"] == case["name"]
            assert data["price"] == case["price"]

    def test_price_never_modified(self):
        """Test prices are never modified."""
        prices = [10.5, 20.25, 0.99, 100.01]
        
        for price in prices:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price

    def test_name_never_modified(self):
        """Test names are never modified."""
        names = ["exact", "EXACT", "eXaCt", "exÀct"]
        
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name


class TestErrorMessages:
    """Test error message accuracy."""

    def test_price_error_message_accuracy(self):
        """Test price error message is accurate."""
        r = client.post("/items", json={"name": "test", "price": -5})
        assert r.status_code == 400
        detail = r.json()["detail"]
        assert "price" in detail.lower()
        assert "0" in detail or "positive" in detail.lower() or ">" in detail

    def test_not_found_error_message_accuracy(self):
        """Test not found error message is accurate."""
        r = client.get("/items/999")
        assert r.status_code == 404
        detail = r.json()["detail"]
        assert "not found" in detail.lower()

    def test_validation_error_exists(self):
        """Test validation error has detail."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        assert "detail" in r.json()


class TestConcurrentPathIds:
    """Test operations with different path parameter values."""

    @pytest.mark.parametrize("item_id", [1, 2, 3, 4, 5, 10, 100])
    def test_get_different_ids(self, item_id):
        """Test getting different item IDs."""
        r = client.get(f"/items/{item_id}")
        if item_id == 1:
            assert r.status_code == 200
        else:
            assert r.status_code == 404


class TestResponseFieldOrder:
    """Test response fields are present (order may vary)."""

    def test_create_response_has_id_name_price(self):
        """Test create response has all fields."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        assert all(key in data for key in ["id", "name", "price"])

    def test_get_response_has_id_name_price(self):
        """Test get response has all fields."""
        r = client.get("/items/1")
        data = r.json()
        assert all(key in data for key in ["id", "name", "price"])

    def test_health_response_has_status(self):
        """Test health response has status field."""
        r = client.get("/health")
        data = r.json()
        assert "status" in data


class TestTypeValidation:
    """Test type validation in responses."""

    def test_id_is_integer(self):
        """Test response ID is always integer."""
        test_cases = [
            {"name": "a", "price": 1.0},
            {"name": "b", "price": 0.01},
            {"name": "c", "price": 1e6},
        ]
        for case in test_cases:
            r = client.post("/items", json=case)
            assert isinstance(r.json()["id"], int)

    def test_name_is_string(self):
        """Test response name is always string."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert isinstance(r.json()["name"], str)

    def test_price_is_number(self):
        """Test response price is a number."""
        r = client.post("/items", json={"name": "test", "price": 10.5})
        price = r.json()["price"]
        assert isinstance(price, (int, float))

    def test_status_is_string(self):
        """Test health status is string."""
        r = client.get("/health")
        assert isinstance(r.json()["status"], str)
