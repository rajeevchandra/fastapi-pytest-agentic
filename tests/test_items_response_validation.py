import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes for POST /items endpoint."""

    def test_create_item_success_returns_200(self):
        """Test successful item creation returns 200 OK."""
        response = client.post("/items", json={"name": "item", "price": 10.0})
        assert response.status_code == 200

    def test_create_item_invalid_price_returns_400(self):
        """Test invalid price returns 400 Bad Request."""
        response = client.post("/items", json={"name": "item", "price": 0})
        assert response.status_code == 400

    def test_create_item_negative_price_returns_400(self):
        """Test negative price returns 400 Bad Request."""
        response = client.post("/items", json={"name": "item", "price": -10})
        assert response.status_code == 400

    def test_create_item_missing_field_returns_422(self):
        """Test missing required field returns 422 Unprocessable Entity."""
        response = client.post("/items", json={"name": "item"})
        assert response.status_code == 422

    @pytest.mark.parametrize("name,price", [
        ("item1", 10.0),
        ("item2", 99.99),
        ("item3", 0.01),
    ])
    def test_create_item_multiple_success_cases(self, name, price):
        """Test multiple successful item creation scenarios."""
        response = client.post("/items", json={"name": name, "price": price})
        assert response.status_code == 200


class TestCreateItemErrorResponses:
    """Test error response format for POST /items endpoint."""

    def test_invalid_price_error_has_detail(self):
        """Test 400 error includes detail message."""
        response = client.post("/items", json={"name": "item", "price": 0})
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_invalid_price_error_message_content(self):
        """Test 400 error message clearly indicates the problem."""
        response = client.post("/items", json={"name": "item", "price": 0})
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "price" in detail.lower()

    def test_missing_field_error_has_detail(self):
        """Test 422 error includes detail message."""
        response = client.post("/items", json={"price": 10.0})
        assert response.status_code == 422
        data = response.json()
        # 422 response may have different structure (detail array or object)
        assert "detail" in data or "errors" in data or len(data) > 0

    def test_error_response_is_json(self):
        """Test error responses are valid JSON."""
        response = client.post("/items", json={"name": "item", "price": -5})
        assert response.status_code == 400
        # Should not raise exception
        response.json()

    def test_error_response_content_type(self):
        """Test error response has JSON content type."""
        response = client.post("/items", json={"name": "item", "price": 0})
        assert response.status_code == 400
        assert "application/json" in response.headers.get("content-type", "")


class TestGetItemHTTPStatusCodes:
    """Test HTTP status codes for GET /items/{item_id} endpoint."""

    def test_get_item_found_returns_200(self):
        """Test found item returns 200 OK."""
        response = client.get("/items/1")
        assert response.status_code == 200

    def test_get_item_not_found_returns_404(self):
        """Test missing item returns 404 Not Found."""
        response = client.get("/items/2")
        assert response.status_code == 404

    @pytest.mark.parametrize("item_id", [2, 3, 100, 999])
    def test_get_item_various_not_found_ids(self, item_id):
        """Test various non-existent item IDs return 404."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404

    def test_get_item_found_item_returns_200(self):
        """Test item_id=1 (which exists) returns 200."""
        response = client.get("/items/1")
        assert response.status_code == 200


class TestGetItemErrorResponses:
    """Test error response format for GET /items/{item_id} endpoint."""

    def test_get_item_not_found_has_detail(self):
        """Test 404 error includes detail message."""
        response = client.get("/items/999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_get_item_not_found_error_message(self):
        """Test 404 error message indicates resource not found."""
        response = client.get("/items/999")
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert "not found" in detail.lower() or "404" in detail

    def test_get_item_error_response_is_json(self):
        """Test 404 response is valid JSON."""
        response = client.get("/items/999")
        assert response.status_code == 404
        # Should not raise exception
        response.json()


class TestResponseStructureSuccessItems:
    """Test response structure for successful POST /items responses."""

    def test_create_item_response_structure(self):
        """Test POST /items response has correct structure."""
        response = client.post("/items", json={"name": "book", "price": 15.5})
        assert response.status_code == 200
        data = response.json()
        # Must have exactly these fields
        assert set(data.keys()) == {"id", "name", "price"}

    def test_create_item_response_field_order(self):
        """Test response field values match input."""
        input_data = {"name": "laptop", "price": 999.99}
        response = client.post("/items", json=input_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == input_data["name"]
        assert data["price"] == input_data["price"]

    def test_create_item_id_field_is_integer(self):
        """Test id field in response is an integer."""
        response = client.post("/items", json={"name": "item", "price": 10.0})
        assert response.status_code == 200
        assert isinstance(response.json()["id"], int)

    def test_create_item_name_field_is_string(self):
        """Test name field in response is a string."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        assert isinstance(response.json()["name"], str)

    def test_create_item_price_field_is_numeric(self):
        """Test price field in response is numeric."""
        response = client.post("/items", json={"name": "item", "price": 25.5})
        assert response.status_code == 200
        price = response.json()["price"]
        assert isinstance(price, (int, float))


class TestResponseStructureGetItem:
    """Test response structure for successful GET /items/{item_id} responses."""

    def test_get_item_response_structure(self):
        """Test GET /items/{item_id} response has correct structure."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        # Must have these fields
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_id_field_is_integer(self):
        """Test id field in GET response is an integer."""
        response = client.get("/items/1")
        assert response.status_code == 200
        assert isinstance(response.json()["id"], int)

    def test_get_item_name_field_is_string(self):
        """Test name field in GET response is a string."""
        response = client.get("/items/1")
        assert response.status_code == 200
        assert isinstance(response.json()["name"], str)

    def test_get_item_price_field_is_numeric(self):
        """Test price field in GET response is numeric."""
        response = client.get("/items/1")
        assert response.status_code == 200
        price = response.json()["price"]
        assert isinstance(price, (int, float))


class TestResponseContentType:
    """Test response content types."""

    def test_create_item_response_is_json(self):
        """Test POST /items response content type is JSON."""
        response = client.post("/items", json={"name": "item", "price": 10.0})
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_get_item_response_is_json(self):
        """Test GET /items/{item_id} response content type is JSON."""
        response = client.get("/items/1")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_error_response_is_json(self):
        """Test error responses have JSON content type."""
        response = client.post("/items", json={"name": "item", "price": 0})
        assert response.status_code == 400
        assert "application/json" in response.headers.get("content-type", "")


class TestResponseConsistency:
    """Test consistency across multiple responses."""

    def test_get_found_item_consistency(self):
        """Test multiple GET requests for same item return consistent data."""
        response1 = client.get("/items/1")
        response2 = client.get("/items/1")
        assert response1.status_code == response2.status_code == 200
        assert response1.json() == response2.json()

    def test_error_response_consistency(self):
        """Test multiple error requests return consistent error format."""
        response1 = client.post("/items", json={"name": "item", "price": 0})
        response2 = client.post("/items", json={"name": "item", "price": 0})
        assert response1.status_code == response2.status_code == 400
        # Both should have detail field
        assert "detail" in response1.json()
        assert "detail" in response2.json()

    def test_create_item_always_returns_full_structure(self):
        """Test all successful creates return complete response structure."""
        test_cases = [
            {"name": "book", "price": 10.0},
            {"name": "pen", "price": 1.5},
            {"name": "notebook", "price": 5.0},
        ]
        for test_case in test_cases:
            response = client.post("/items", json=test_case)
            assert response.status_code == 200
            data = response.json()
            assert set(data.keys()) == {"id", "name", "price"}
