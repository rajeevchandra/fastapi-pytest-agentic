import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemResponse:
    """Test response structure and data types for create_item endpoint."""

    def test_create_item_response_status_200(self):
        """Test successful create_item returns 200 status."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200

    def test_create_item_response_content_type(self):
        """Test create_item response has JSON content type."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert "application/json" in response.headers.get("content-type", "")

    @pytest.mark.parametrize("name,price", [
        ("item1", 5.0),
        ("item2", 100.5),
        ("test", 0.01),
    ])
    def test_create_item_returns_correct_data(self, name, price):
        """Test create_item returns the posted data in response."""
        response = client.post("/items", json={"name": name, "price": price})
        data = response.json()
        assert data["name"] == name
        assert data["price"] == price


class TestCreateItemErrorResponse:
    """Test error response format for create_item endpoint."""

    def test_create_item_invalid_price_error_status(self):
        """Test create_item returns 400 for invalid price."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400

    def test_create_item_invalid_price_error_detail(self):
        """Test create_item error response has correct detail message."""
        response = client.post("/items", json={"name": "test", "price": -5})
        error_data = response.json()
        assert "detail" in error_data
        assert error_data["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [0, -1, -100])
    def test_create_item_all_invalid_prices_have_detail(self, price):
        """Test all invalid prices return detail in error response."""
        response = client.post("/items", json={"name": "test", "price": price})
        error_data = response.json()
        assert "detail" in error_data
        assert isinstance(error_data["detail"], str)


class TestGetItemResponse:
    """Test response structure and data types for get_item endpoint."""

    def test_get_item_found_status(self):
        """Test get_item returns 200 for existing item."""
        response = client.get("/items/1")
        assert response.status_code == 200

    def test_get_item_found_contains_required_fields(self):
        """Test get_item response contains all required fields."""
        response = client.get("/items/1")
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_found_field_types(self):
        """Test get_item response fields have correct types."""
        response = client.get("/items/1")
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_found_values(self):
        """Test get_item returns expected values."""
        response = client.get("/items/1")
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0


class TestGetItemNotFound:
    """Test not found scenario for get_item endpoint."""

    @pytest.mark.parametrize("item_id", [2, 3, 100, 999])
    def test_get_item_not_found_status(self, item_id):
        """Test get_item returns 404 for non-existent items."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404

    def test_get_item_not_found_error_detail(self):
        """Test get_item not found response has correct detail message."""
        response = client.get("/items/2")
        error_data = response.json()
        assert "detail" in error_data
        assert error_data["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [0, -1, -100, 2, 999])
    def test_get_item_not_found_all_items_have_detail(self, item_id):
        """Test all non-existent items return detail in error response."""
        response = client.get(f"/items/{item_id}")
        if response.status_code == 404:
            error_data = response.json()
            assert "detail" in error_data
            assert isinstance(error_data["detail"], str)


class TestGetItemEdgeCases:
    """Test edge cases for get_item endpoint."""

    def test_get_item_with_negative_id(self):
        """Test get_item with negative item_id returns 404."""
        response = client.get("/items/-1")
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"

    def test_get_item_with_zero_id(self):
        """Test get_item with item_id=0 returns 404."""
        response = client.get("/items/0")
        assert response.status_code == 404

    def test_get_item_with_large_id(self):
        """Test get_item with very large item_id returns 404."""
        response = client.get("/items/999999999")
        assert response.status_code == 404

    @pytest.mark.parametrize("item_id", [1])
    def test_get_item_valid_id_returns_200(self, item_id):
        """Test get_item returns 200 only for item_id=1."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 200


class TestHealthEndpoint:
    """Test health check endpoint responses."""

    def test_health_status_200(self):
        """Test health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self):
        """Test health endpoint response has correct structure."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_health_response_type(self):
        """Test health endpoint returns correct data type."""
        response = client.get("/health")
        data = response.json()
        assert isinstance(data, dict)
        assert isinstance(data["status"], str)


class TestResponseConsistency:
    """Test consistency of responses across multiple calls."""

    def test_multiple_create_calls_consistent_structure(self):
        """Test multiple create_item calls return consistent structure."""
        response1 = client.post("/items", json={"name": "test1", "price": 5.0})
        response2 = client.post("/items", json={"name": "test2", "price": 10.0})
        
        data1 = response1.json()
        data2 = response2.json()
        
        assert set(data1.keys()) == set(data2.keys())
        assert all(k in data2 for k in data1.keys())

    def test_get_item_consistent_structure(self):
        """Test get_item returns consistent structure."""
        response1 = client.get("/items/1")
        response2 = client.get("/items/1")
        
        data1 = response1.json()
        data2 = response2.json()
        
        assert data1 == data2
        assert set(data1.keys()) == set(data2.keys())

    def test_error_response_structure_consistency(self):
        """Test error responses have consistent structure."""
        response1 = client.post("/items", json={"name": "test", "price": 0})
        response2 = client.post("/items", json={"name": "test", "price": -1})
        response3 = client.get("/items/2")
        
        error1 = response1.json()
        error2 = response2.json()
        error3 = response3.json()
        
        assert "detail" in error1
        assert "detail" in error2
        assert "detail" in error3
