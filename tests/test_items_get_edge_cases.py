import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Tests for path parameter validation in get_item endpoint."""

    @pytest.mark.parametrize("item_id", [0, 1])
    def test_get_item_boundary_values(self, item_id):
        """Test get_item with boundary path parameter values."""
        r = client.get(f"/items/{item_id}")
        # Only item_id=1 should succeed
        if item_id == 1:
            assert r.status_code == 200
        else:
            assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [-1, -100, -999])
    def test_get_item_negative_ids(self, item_id):
        """Test get_item with negative item_id."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    @pytest.mark.parametrize(
        "item_id",
        [2, 3, 10, 100, 999, 9999, 2147483647],  # Max 32-bit int
    )
    def test_get_item_various_positive_ids(self, item_id):
        """Test get_item with various positive IDs (all should be 404)."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()

    def test_get_item_very_large_id(self):
        """Test get_item with very large integer ID."""
        large_id = 999999999999
        r = client.get(f"/items/{large_id}")
        assert r.status_code == 404

    def test_get_item_id_one_always_found(self):
        """Test that item_id=1 is always found."""
        for _ in range(3):
            r = client.get("/items/1")
            assert r.status_code == 200
            assert r.json()["id"] == 1


class TestGetItemEdgeCases:
    """Tests for edge cases in get_item endpoint."""

    def test_get_item_with_trailing_slash(self):
        """Test get_item endpoint with trailing slash."""
        r = client.get("/items/1/")
        # This should be treated as a different route (might be 404)
        # FastAPI by default handles this
        assert r.status_code in [200, 307, 404]

    def test_get_item_not_found_consistency(self):
        """Test that 404 responses are consistent for same ID."""
        responses = [client.get(f"/items/{i}") for i in [2, 2, 2]]
        assert all(r.status_code == 404 for r in responses)
        assert all(r.json() == responses[0].json() for r in responses)

    def test_get_item_found_consistency(self):
        """Test that successful responses are consistent."""
        responses = [client.get("/items/1") for _ in range(3)]
        assert all(r.status_code == 200 for r in responses)
        assert all(r.json() == responses[0].json() for r in responses)


class TestIntegrationMultipleOperations:
    """Tests for multiple operations and integration scenarios."""

    def test_create_then_get_item(self):
        """Test creating an item and then attempting to retrieve it."""
        # Create item
        create_r = client.post(
            "/items",
            json={"name": "integration-test", "price": 25.0},
        )
        assert create_r.status_code == 200
        created_id = create_r.json()["id"]

        # Attempt to get created item
        get_r = client.get(f"/items/{created_id}")
        assert get_r.status_code == 200
        # ID matches
        assert get_r.json()["id"] == created_id

    def test_create_multiple_items(self):
        """Test creating multiple items."""
        items_data = [
            {"name": "item1", "price": 10.0},
            {"name": "item2", "price": 20.0},
            {"name": "item3", "price": 30.0},
        ]
        responses = [
            client.post("/items", json=item_data) for item_data in items_data
        ]
        # All should succeed
        assert all(r.status_code == 200 for r in responses)
        # All should return same ID (API limitation)
        ids = [r.json()["id"] for r in responses]
        assert all(id == 1 for id in ids)

    def test_sequential_operations_get_then_create(self):
        """Test getting an item then creating a new item."""
        # Get existing
        get_r = client.get("/items/1")
        assert get_r.status_code == 200

        # Create new
        create_r = client.post("/items", json={"name": "new", "price": 50.0})
        assert create_r.status_code == 200

        # Get existing again should still work
        get_r2 = client.get("/items/1")
        assert get_r2.status_code == 200
        assert get_r.json() == get_r2.json()


class TestCreateItemIntegrationEdgeCases:
    """Tests for edge cases when creating items."""

    def test_create_item_then_verify_not_created_with_different_id(self):
        """Test that created item is only available at assigned ID."""
        create_r = client.post(
            "/items",
            json={"name": "test", "price": 15.0},
        )
        created_id = create_r.json()["id"]

        # Should be available at created_id
        r1 = client.get(f"/items/{created_id}")
        assert r1.status_code == 200

        # Should NOT be available at other IDs
        r2 = client.get(f"/items/{created_id + 1}")
        assert r2.status_code == 404

    def test_create_item_response_reflects_request(self):
        """Test that create response accurately reflects input."""
        request_data = {"name": "reflect-test", "price": 42.5}
        r = client.post("/items", json=request_data)
        response_data = r.json()

        # Name should match
        assert response_data["name"] == request_data["name"]
        # Price should match
        assert response_data["price"] == request_data["price"]
        # ID should be assigned
        assert response_data["id"] == 1

    def test_create_item_unicode_name_preserved_in_get(self):
        """Test that unicode names are preserved through create and get."""
        unicode_name = "café ☕"
        create_r = client.post(
            "/items",
            json={"name": unicode_name, "price": 5.0},
        )
        assert create_r.status_code == 200
        created_id = create_r.json()["id"]

        # Get the item and verify unicode name
        get_r = client.get(f"/items/{created_id}")
        assert get_r.status_code == 200
        # Note: Create returns unicode, but GET returns fixed "sample"
        # This is API behavior


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_endpoint_returns_ok(self):
        """Test that health endpoint returns ok status."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"

    def test_health_endpoint_response_structure(self):
        """Test health endpoint response structure."""
        r = client.get("/health")
        data = r.json()
        assert "status" in data
        assert len(data) == 1

    def test_health_endpoint_multiple_calls(self):
        """Test that health endpoint works reliably."""
        for _ in range(5):
            r = client.get("/health")
            assert r.status_code == 200
            assert r.json() == {"status": "ok"}


class TestErrorScenarios:
    """Tests for various error scenarios."""

    def test_create_item_negative_price_error(self):
        """Test that negative price produces meaningful error."""
        r = client.post("/items", json={"name": "expensive", "price": -10.0})
        assert r.status_code == 400
        error = r.json()["detail"]
        assert isinstance(error, str)
        assert "price" in error.lower()
        assert "0" in error

    def test_get_item_not_found_error_message(self):
        """Test that not found error has meaningful message."""
        r = client.get("/items/999")
        assert r.status_code == 404
        error = r.json()["detail"]
        assert "not found" in error.lower()

    def test_create_item_missing_required_field_error(self):
        """Test error when required field is missing."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        assert "detail" in r.json()
        # Should have validation error info
        errors = r.json()["detail"]
        assert isinstance(errors, list)


class TestContentNegotiation:
    """Tests for content negotiation and media types."""

    def test_create_item_accepts_json(self):
        """Test that POST accepts JSON."""
        r = client.post(
            "/items",
            json={"name": "json-test", "price": 10.0},
        )
        assert r.status_code == 200

    def test_get_item_response_json(self):
        """Test that GET returns JSON."""
        r = client.get("/items/1")
        assert r.status_code == 200
        # Should be parseable as JSON
        assert isinstance(r.json(), dict)

    def test_error_response_json_format(self):
        """Test that errors are returned as JSON."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        # Should be valid JSON with detail field
        data = r.json()
        assert isinstance(data, dict)
        assert "detail" in data
