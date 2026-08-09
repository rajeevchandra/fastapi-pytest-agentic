"""Path parameter and integration edge cases for items endpoint."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get_item."""

    @pytest.mark.parametrize("item_id", [1])
    def test_valid_item_id_found(self, item_id):
        """Test that valid item ID returns the item."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200
        assert r.json()["id"] == item_id

    @pytest.mark.parametrize("item_id", [0, -1, -100, 2, 3, 999])
    def test_nonexistent_item_ids(self, item_id):
        """Test that non-existent item IDs return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_item_id_zero_not_found(self):
        """Test that item ID 0 returns 404."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_item_id_negative(self):
        """Test that negative item IDs return 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_large_item_id(self):
        """Test that very large item IDs return 404."""
        r = client.get("/items/999999")
        assert r.status_code == 404


class TestCreateItemIdGeneration:
    """Test ID generation in create_item."""

    def test_created_item_has_id_one(self):
        """Test that created items always have ID 1."""
        r = client.post("/items", json={"name": "first", "price": 5.0})
        assert r.json()["id"] == 1

    def test_sequential_creates_have_same_id(self):
        """Test that sequential creates all return ID 1."""
        ids = []
        for i in range(5):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            ids.append(r.json()["id"])
        assert all(id == 1 for id in ids)


class TestCreateAndRetrieve:
    """Test create and retrieve integration."""

    def test_create_item_then_retrieve(self):
        """Test that created item can be retrieved."""
        # Create item with specific values
        create_r = client.post("/items", json={"name": "test", "price": 15.0})
        assert create_r.status_code == 200
        created = create_r.json()

        # Retrieve item
        get_r = client.get(f"/items/{created['id']}")
        assert get_r.status_code == 200

    def test_created_item_not_in_get_response(self):
        """Test that get_item returns fixed response, not created items."""
        # Create item
        create_r = client.post("/items", json={"name": "custom", "price": 99.99})
        assert create_r.status_code == 200
        created = create_r.json()

        # Get item - should return fixed response, not what we created
        get_r = client.get(f"/items/{created['id']}")
        retrieved = get_r.json()
        # The response is fixed, not based on what was created
        assert retrieved["name"] == "sample"  # fixed value
        assert retrieved["price"] == 10.0     # fixed value


class TestIntegrationScenarios:
    """Test integration scenarios with multiple operations."""

    def test_multiple_create_then_get(self):
        """Test multiple creates followed by gets."""
        for i in range(3):
            create_r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert create_r.status_code == 200

        # Get item 1 should still work
        get_r = client.get("/items/1")
        assert get_r.status_code == 200

        # Get other IDs should 404
        get_r2 = client.get("/items/2")
        assert get_r2.status_code == 404

    def test_create_with_various_names_and_prices(self):
        """Test creates with various name and price combinations."""
        test_cases = [
            ("apple", 1.50),
            ("book", 25.99),
            ("123", 0.01),
            ("", 999.99),
        ]
        for name, price in test_cases:
            r = client.post("/items", json={"name": name, "price": price})
            assert r.status_code == 200
            assert r.json()["name"] == name
            assert r.json()["price"] == price

    def test_interleaved_create_and_get(self):
        """Test interleaved create and get operations."""
        create_r = client.post("/items", json={"name": "test1", "price": 5.0})
        assert create_r.status_code == 200

        get_r = client.get("/items/1")
        assert get_r.status_code == 200

        create_r2 = client.post("/items", json={"name": "test2", "price": 10.0})
        assert create_r2.status_code == 200

        get_r2 = client.get("/items/1")
        assert get_r2.status_code == 200

        get_r3 = client.get("/items/2")
        assert get_r3.status_code == 404


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_endpoint_returns_ok(self):
        """Test that health endpoint returns ok status."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_endpoint_response_format(self):
        """Test that health endpoint has correct response format."""
        r = client.get("/health")
        data = r.json()
        assert "status" in data
        assert isinstance(data["status"], str)

    def test_health_endpoint_consistency(self):
        """Test that health endpoint returns consistent responses."""
        for _ in range(3):
            r = client.get("/health")
            assert r.status_code == 200
            assert r.json() == {"status": "ok"}


class TestErrorMessages:
    """Test error message consistency."""

    def test_price_validation_error_message(self):
        """Test that price validation error has correct message."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_not_found_error_message(self):
        """Test that not found error has correct message."""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_error_messages_exact_match(self):
        """Test that error messages match exactly."""
        # Price error
        r1 = client.post("/items", json={"name": "a", "price": -5})
        assert r1.json()["detail"] == "price must be > 0"

        r2 = client.post("/items", json={"name": "b", "price": 0.0})
        assert r2.json()["detail"] == "price must be > 0"

        # Not found error
        r3 = client.get("/items/100")
        assert r3.json()["detail"] == "not found"

        r4 = client.get("/items/999")
        assert r4.json()["detail"] == "not found"
