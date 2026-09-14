"""Test path parameters, edge cases, and integration scenarios."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for GET /items/{item_id}."""

    @pytest.mark.parametrize("item_id", [-1000, -100, -1, 0])
    def test_get_item_negative_and_zero_ids(self, item_id):
        """Negative and zero item IDs should be treated as not found."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [2, 3, 5, 10, 50, 100, 1000, 999999])
    def test_get_item_various_positive_ids_not_found(self, item_id):
        """All IDs except 1 should return 404."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404

    def test_get_item_id_boundary_max_int(self):
        """Very large item IDs should return 404."""
        response = client.get(f"/items/{2147483647}")  # Max 32-bit int
        assert response.status_code == 404

    def test_get_item_id_1_found(self):
        """Only item_id = 1 should be found."""
        response = client.get("/items/1")
        assert response.status_code == 200


class TestGetItemResponseFields:
    """Test that get_item response has consistent field values."""

    def test_get_item_1_response_structure(self):
        """Item 1 should have specific expected values."""
        response = client.get("/items/1")
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_1_response_all_fields(self):
        """Response must have id, name, and price fields."""
        response = client.get("/items/1")
        data = response.json()
        required_fields = {"id", "name", "price"}
        assert required_fields.issubset(data.keys())

    @pytest.mark.parametrize("item_id", [1])
    def test_get_item_single_id_success(self, item_id):
        """Item ID 1 should be successfully retrieved."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 200


class TestCreateItemPriceEdgeCases:
    """Test edge cases and boundary values for price field."""

    def test_create_item_smallest_positive_price(self):
        """Very small positive price should be accepted."""
        response = client.post("/items", json={"name": "tiny", "price": 0.001})
        assert response.status_code == 200
        assert response.json()["price"] == 0.001

    def test_create_item_very_large_price(self):
        """Very large prices should be accepted."""
        response = client.post("/items", json={"name": "expensive", "price": 1e15})
        assert response.status_code == 200
        assert response.json()["price"] == 1e15

    def test_create_item_price_exactly_zero_fails(self):
        """Price exactly 0.0 should fail."""
        response = client.post("/items", json={"name": "free", "price": 0.0})
        assert response.status_code == 400

    def test_create_item_price_just_above_zero_succeeds(self):
        """Price just above zero should succeed."""
        response = client.post("/items", json={"name": "cheap", "price": 0.00001})
        assert response.status_code == 200
        assert response.json()["price"] == 0.00001


class TestCreateItemNameEdgeCases:
    """Test edge cases and boundary values for name field."""

    def test_create_item_empty_name_accepted(self):
        """Empty string name should be accepted."""
        response = client.post("/items", json={"name": "", "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == ""

    def test_create_item_single_char_name(self):
        """Single character name should be accepted."""
        response = client.post("/items", json={"name": "X", "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == "X"

    def test_create_item_max_length_name(self):
        """Very long name strings should be accepted."""
        long_name = "x" * 5000
        response = client.post("/items", json={"name": long_name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == long_name
        assert len(response.json()["name"]) == 5000

    @pytest.mark.parametrize("name", ["中文", "العربية", "Русский", "🚀📱💻"])
    def test_create_item_unicode_names(self, name):
        """Unicode and emoji names should be accepted."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == name


class TestCreateItemResponseIdField:
    """Test ID field in create item response."""

    def test_create_item_returns_id_one(self):
        """Create item endpoint should always return id=1."""
        response = client.post("/items", json={"name": "item", "price": 10.0})
        assert response.json()["id"] == 1

    def test_create_item_id_is_integer(self):
        """ID should be an integer type."""
        response = client.post("/items", json={"name": "item", "price": 10.0})
        data = response.json()
        assert isinstance(data["id"], int)

    @pytest.mark.parametrize("name,price", [
        ("apple", 1.5),
        ("book", 25.99),
        ("pen", 0.5),
    ])
    def test_create_item_consistent_id(self, name, price):
        """Multiple creates should all return id=1."""
        response = client.post("/items", json={"name": name, "price": price})
        assert response.json()["id"] == 1


class TestHealthEndpointEdgeCases:
    """Test health endpoint edge cases."""

    def test_health_endpoint_always_ok(self):
        """Health endpoint should always return ok status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_health_endpoint_json_format(self):
        """Health response should be valid JSON object."""
        response = client.get("/health")
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) >= 1

    @pytest.mark.parametrize("_", range(5))
    def test_health_endpoint_multiple_calls(self, _):
        """Health endpoint should be consistent across multiple calls."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestIntegrationScenarios:
    """Test integration scenarios and multi-step workflows."""

    def test_create_and_get_item_sequence(self):
        """Create item then attempt to get it (should get hardcoded item 1)."""
        # Create an item
        create_response = client.post("/items", json={"name": "created", "price": 20.0})
        assert create_response.status_code == 200
        created_item = create_response.json()
        
        # Get item 1 (which is hardcoded in the endpoint)
        get_response = client.get("/items/1")
        assert get_response.status_code == 200
        retrieved_item = get_response.json()
        
        # Verify structure consistency
        assert created_item["id"] == 1
        assert retrieved_item["id"] == 1

    def test_multiple_creates_same_id(self):
        """Multiple create operations should all return same id=1."""
        responses = []
        for i in range(3):
            response = client.post(
                "/items", 
                json={"name": f"item_{i}", "price": 10.0 + i}
            )
            responses.append(response)
        
        # All should succeed and return id=1
        for response in responses:
            assert response.status_code == 200
            assert response.json()["id"] == 1

    def test_error_recovery_after_validation_error(self):
        """API should handle validation errors and accept valid requests."""
        # Invalid request
        invalid = client.post("/items", json={"price": 10.0})  # Missing name
        assert invalid.status_code == 422
        
        # Valid request after error
        valid = client.post("/items", json={"name": "item", "price": 10.0})
        assert valid.status_code == 200

    def test_error_recovery_after_business_logic_error(self):
        """API should handle business logic errors and accept valid requests."""
        # Invalid price
        invalid = client.post("/items", json={"name": "item", "price": -5})
        assert invalid.status_code == 400
        
        # Valid request after error
        valid = client.post("/items", json={"name": "item", "price": 10.0})
        assert valid.status_code == 200


class TestResponseTypeConsistency:
    """Test type consistency across endpoints."""

    @pytest.mark.parametrize("price", [1, 5.5, 100.25])
    def test_price_type_consistency_create_endpoint(self, price):
        """Created item price type should match response."""
        response = client.post("/items", json={"name": "item", "price": price})
        returned_price = response.json()["price"]
        # Price should be numeric
        assert isinstance(returned_price, (int, float))
        assert returned_price == price

    def test_name_string_type_consistency(self):
        """Name should always be string type in responses."""
        response = client.post("/items", json={"name": "test", "price": 10})
        assert isinstance(response.json()["name"], str)

    def test_get_item_response_types(self):
        """GET /items/{id} response should have consistent types."""
        response = client.get("/items/1")
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))


class TestMethodValidation:
    """Test HTTP method validation."""

    def test_health_get_only(self):
        """Health endpoint should respond to GET."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_create_item_post_only(self):
        """Create item endpoint should respond to POST."""
        response = client.post("/items", json={"name": "item", "price": 10.0})
        assert response.status_code == 200

    def test_get_item_get_only(self):
        """Get item endpoint should respond to GET."""
        response = client.get("/items/1")
        assert response.status_code == 200
