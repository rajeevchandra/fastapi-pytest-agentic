import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemBoundaryValues:
    """Test boundary values for GET /items/{item_id} endpoint"""

    def test_get_item_id_zero(self):
        """Test that item_id=0 returns 404 (not found)"""
        r = client.get("/items/0")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_negative(self):
        """Test that negative item_id returns 404 (not found)"""
        r = client.get("/items/-1")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_large_negative(self):
        """Test that large negative item_id returns 404"""
        r = client.get("/items/-999999")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_very_large_positive(self):
        """Test that very large item_id returns 404"""
        r = client.get("/items/999999999")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_max_int(self):
        """Test that maximum integer value returns 404"""
        r = client.get("/items/2147483647")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"


class TestGetItemSuccessful:
    """Test successful GET /items/{item_id} responses"""

    def test_get_item_found_id_1(self):
        """Test successful retrieval of item with id=1"""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_response_structure(self):
        """Test that response contains all required fields"""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], float)

    def test_get_item_response_content_type(self):
        """Test that response content type is JSON"""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "application/json" in r.headers["content-type"]


class TestGetItemNotFound:
    """Test 404 responses for GET /items/{item_id} endpoint"""

    def test_get_item_id_2_not_found(self):
        """Test that item_id=2 returns 404"""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_3_not_found(self):
        """Test that item_id=3 returns 404"""
        r = client.get("/items/3")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_100_not_found(self):
        """Test that item_id=100 returns 404"""
        r = client.get("/items/100")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_error_response_structure(self):
        """Test that error response has proper structure"""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)


class TestGetItemInvalidPathParameter:
    """Test invalid path parameter formats"""

    def test_get_item_string_id(self):
        """Test that string item_id is handled"""
        r = client.get("/items/abc")
        # FastAPI validates path parameters, should return 422 or similar
        assert r.status_code in [422, 400]

    def test_get_item_float_id(self):
        """Test that float item_id is handled"""
        r = client.get("/items/1.5")
        # FastAPI's path parameter validation handles this
        assert r.status_code in [422, 400, 404]

    def test_get_item_special_chars_id(self):
        """Test that special characters in item_id are handled"""
        r = client.get("/items/!@#$")
        assert r.status_code in [422, 400]


class TestGetItemResponseValidation:
    """Test response data validation for GET /items/{item_id}"""

    def test_get_item_id_field_is_integer(self):
        """Test that id field is an integer"""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)

    def test_get_item_name_field_is_string(self):
        """Test that name field is a string"""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["name"], str)
        assert len(data["name"]) > 0

    def test_get_item_price_field_is_float(self):
        """Test that price field is a float"""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["price"], float)
        assert data["price"] > 0

    def test_get_item_no_extra_fields(self):
        """Test that response contains only expected fields"""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        expected_fields = {"id", "name", "price"}
        assert set(data.keys()) == expected_fields


class TestGetItemParametrized:
    """Parametrized tests for comprehensive GET endpoint coverage"""

    @pytest.mark.parametrize("item_id", [2, 3, 10, 100, 999, 999999])
    def test_various_ids_not_found(self, item_id):
        """Test that non-1 item IDs return 404"""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [-1, -100, -999999])
    def test_negative_ids_not_found(self, item_id):
        """Test that negative item IDs return 404"""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [1])
    def test_valid_id_found(self, item_id):
        """Test that item_id=1 returns valid response"""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == item_id
        assert "name" in data
        assert "price" in data


class TestGetItemErrorHandling:
    """Test error handling and edge cases"""

    def test_get_item_not_found_error_detail(self):
        """Test that 404 error detail message is clear"""
        r = client.get("/items/999")
        assert r.status_code == 404
        error = r.json()
        assert error["detail"] == "not found"

    def test_get_item_invalid_format_error_response(self):
        """Test that invalid format returns proper error"""
        r = client.get("/items/invalid")
        assert r.status_code in [422, 400]
        # Should have an error response
        assert r.text

    def test_get_item_whitespace_id(self):
        """Test that whitespace in path is handled"""
        # FastAPI routing will not match this
        r = client.get("/items/ ")
        assert r.status_code in [422, 400, 404]
