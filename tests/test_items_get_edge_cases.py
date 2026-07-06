from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


class TestGetItemBoundaryValues:
    """Test boundary values for get_item endpoint"""

    def test_get_item_id_zero(self):
        """Test GET with item_id = 0 (boundary)"""
        r = client.get("/items/0")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_negative(self):
        """Test GET with negative item_id"""
        r = client.get("/items/-1")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_large_negative(self):
        """Test GET with large negative item_id"""
        r = client.get("/items/-999")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [0, -1, -10, 2, 3, 100, 999])
    def test_get_item_invalid_ids(self, item_id):
        """Parametrized test for invalid item IDs (all except 1)"""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_very_large_id(self):
        """Test GET with very large item_id"""
        r = client.get("/items/9999999999")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_max_int(self):
        """Test GET with maximum integer value"""
        r = client.get(f"/items/{2**31 - 1}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"


class TestGetItemSuccess:
    """Test successful get_item endpoint scenarios"""

    def test_get_item_id_one_success(self):
        """Test successful GET with item_id = 1"""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_response_structure(self):
        """Test response contains all expected fields"""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert set(data.keys()) == {"id", "name", "price"}

    def test_get_item_response_types(self):
        """Test response field types are correct"""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))


class TestGetItemErrorHandling:
    """Test error handling and edge cases for get_item endpoint"""

    def test_get_item_not_found_response_format(self):
        """Test 404 response has proper error format"""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_get_item_multiple_not_found_requests(self):
        """Test multiple consecutive not-found requests"""
        for item_id in [2, 3, 4, 5]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404
            assert r.json()["detail"] == "not found"

    def test_get_item_alternating_found_not_found(self):
        """Test alternating between found and not found"""
        r = client.get("/items/1")
        assert r.status_code == 200
        
        r = client.get("/items/2")
        assert r.status_code == 404
        
        r = client.get("/items/1")
        assert r.status_code == 200


class TestGetItemContentType:
    """Test content type and response headers"""

    def test_get_item_success_content_type(self):
        """Test success response has JSON content type"""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_item_not_found_content_type(self):
        """Test error response has JSON content type"""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "application/json" in r.headers.get("content-type", "")
