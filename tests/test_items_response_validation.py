import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemResponseStructure:
    """Test response structure and field validation for item creation."""

    def test_create_item_response_has_required_fields(self):
        """Test that response contains all required fields."""
        r = client.post("/items", json={"name": "book", "price": 15.0})
        assert r.status_code == 200
        data = r.json()
        
        # Verify all expected fields exist
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert len(data) == 3  # Only these 3 fields

    def test_create_item_response_field_types(self):
        """Test that response fields have correct types."""
        r = client.post("/items", json={"name": "book", "price": 15.0})
        assert r.status_code == 200
        data = r.json()
        
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    @pytest.mark.parametrize("name,price", [
        ("item1", 10.5),
        ("item2", 0.01),
        ("item3", 999.99),
    ])
    def test_create_item_response_matches_input(self, name, price):
        """Test that response returns the same data as input."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        
        assert data["name"] == name
        assert data["price"] == price
        assert data["id"] is not None

    def test_create_item_response_id_is_consistent(self):
        """Test that all successful responses have the same ID (implementation specific)."""
        r1 = client.post("/items", json={"name": "item1", "price": 10.0})
        r2 = client.post("/items", json={"name": "item2", "price": 20.0})
        
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["id"] == r2.json()["id"] == 1


class TestCreateItemErrorResponses:
    """Test error response structure and consistency."""

    def test_invalid_price_error_has_detail_field(self):
        """Test that error response has detail field."""
        r = client.post("/items", json={"name": "item", "price": -5})
        assert r.status_code == 400
        data = r.json()
        
        assert "detail" in data
        assert isinstance(data["detail"], str)
        assert len(data["detail"]) > 0

    def test_invalid_price_error_message_content(self):
        """Test error message is descriptive."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        detail = r.json()["detail"]
        
        assert "price" in detail.lower()
        assert ">" in detail or "positive" in detail.lower() or "greater" in detail.lower()

    def test_validation_error_has_detail_field(self):
        """Test that validation errors have detail field."""
        r = client.post("/items", json={"price": 10.0})  # missing name
        assert r.status_code == 422
        data = r.json()
        
        assert "detail" in data
        assert isinstance(data["detail"], list)
        assert len(data["detail"]) > 0

    def test_validation_error_contains_field_info(self):
        """Test that validation errors identify the problem field."""
        r = client.post("/items", json={"name": "item"})  # missing price
        assert r.status_code == 422
        detail = r.json()["detail"]
        
        assert len(detail) > 0
        assert any("price" in str(error).lower() for error in detail)

    def test_validation_error_has_type_and_loc(self):
        """Test validation error structure has standard fields."""
        r = client.post("/items", json={"name": 123, "price": 10})
        assert r.status_code == 422
        detail = r.json()["detail"]
        
        assert len(detail) > 0
        first_error = detail[0]
        assert "type" in first_error or "msg" in first_error or "loc" in first_error


class TestGetItemResponseStructure:
    """Test response structure for item retrieval."""

    def test_get_item_response_has_required_fields(self):
        """Test that GET response contains all required fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_response_field_types(self):
        """Test that GET response fields have correct types."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_response_values(self):
        """Test that GET response has expected values."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        
        assert data["id"] == 1
        assert isinstance(data["name"], str)
        assert data["price"] > 0


class TestGetItemErrorResponses:
    """Test error responses for item retrieval."""

    def test_get_item_not_found_has_detail(self):
        """Test that 404 response has detail field."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_get_item_not_found_error_message(self):
        """Test 404 error message is descriptive."""
        r = client.get("/items/2")
        assert r.status_code == 404
        detail = r.json()["detail"]
        
        assert "found" in detail.lower() or "not found" in detail.lower() or "exist" in detail.lower()

    @pytest.mark.parametrize("item_id", [2, 3, 999, 0, -1])
    def test_get_nonexistent_items_return_404(self, item_id):
        """Test that non-existent item_ids return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert "detail" in r.json()


class TestHealthEndpointResponse:
    """Test response structure for health check endpoint."""

    def test_health_response_structure(self):
        """Test health endpoint response format."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        
        assert "status" in data
        assert isinstance(data["status"], str)

    def test_health_response_value(self):
        """Test health endpoint returns correct status."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        
        assert data["status"] == "ok"
        assert len(data) == 1  # Only status field

    def test_health_endpoint_always_succeeds(self):
        """Test health endpoint is always accessible."""
        for _ in range(3):
            r = client.get("/health")
            assert r.status_code == 200
            assert r.json()["status"] == "ok"


class TestHTTPStatusCodes:
    """Test HTTP status code consistency across endpoints."""

    def test_successful_post_returns_200(self):
        """Test successful POST returns 200."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200

    def test_successful_get_returns_200(self):
        """Test successful GET returns 200."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_health_returns_200(self):
        """Test health endpoint returns 200."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_business_error_returns_400(self):
        """Test business logic error returns 400."""
        r = client.post("/items", json={"name": "item", "price": -1})
        assert r.status_code == 400

    def test_not_found_returns_404(self):
        """Test not found error returns 404."""
        r = client.get("/items/999")
        assert r.status_code == 404

    def test_validation_error_returns_422(self):
        """Test validation error returns 422."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    @pytest.mark.parametrize("status_code,scenario", [
        (200, ("post", {"name": "item", "price": 10.0})),
        (404, ("get", None)),
        (400, ("post_bad", {"name": "item", "price": 0})),
    ])
    def test_status_codes_across_scenarios(self, status_code, scenario):
        """Test status codes in various scenarios."""
        if scenario[0] == "post":
            r = client.post("/items", json=scenario[1])
        elif scenario[0] == "post_bad":
            r = client.post("/items", json=scenario[1])
        elif scenario[0] == "get":
            r = client.get("/items/999")
        
        assert r.status_code == status_code
