import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes for create_item endpoint."""

    @pytest.mark.parametrize("name,price,expected_status", [
        ("item1", 10.0, 200),
        ("item2", 0.01, 200),
        ("item3", 999.99, 200),
        ("bad", 0, 400),
        ("bad", -1, 400),
        ("bad", -100.50, 400),
    ])
    def test_create_item_status_codes(self, name, price, expected_status):
        """Test that create_item returns correct HTTP status codes."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == expected_status


class TestGetItemHTTPStatusCodes:
    """Test HTTP status codes for get_item endpoint."""

    @pytest.mark.parametrize("item_id,expected_status", [
        (1, 200),
        (2, 404),
        (3, 404),
        (999, 404),
    ])
    def test_get_item_status_codes(self, item_id, expected_status):
        """Test that get_item returns correct HTTP status codes."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == expected_status


class TestCreateItemResponseContentType:
    """Test response content type for create_item."""

    def test_create_item_returns_json(self):
        """Test that create_item returns JSON content."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.headers.get("content-type") is not None
        assert "application/json" in r.headers.get("content-type", "")

    def test_create_item_error_returns_json(self):
        """Test that error responses are also JSON."""
        r = client.post("/items", json={"name": "bad", "price": 0})
        assert r.headers.get("content-type") is not None
        assert "application/json" in r.headers.get("content-type", "")


class TestGetItemResponseContentType:
    """Test response content type for get_item."""

    def test_get_item_returns_json(self):
        """Test that get_item returns JSON content."""
        r = client.get("/items/1")
        assert r.headers.get("content-type") is not None
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_item_not_found_returns_json(self):
        """Test that not found error is JSON."""
        r = client.get("/items/999")
        assert r.headers.get("content-type") is not None
        assert "application/json" in r.headers.get("content-type", "")


class TestCreateItemResponseFields:
    """Test response field presence and types for create_item."""

    def test_create_item_response_has_id(self):
        """Test that response includes id field."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        assert "id" in data
        assert data["id"] == 1

    def test_create_item_response_has_name(self):
        """Test that response includes name field."""
        r = client.post("/items", json={"name": "myitem", "price": 10.0})
        data = r.json()
        assert "name" in data
        assert data["name"] == "myitem"

    def test_create_item_response_has_price(self):
        """Test that response includes price field."""
        r = client.post("/items", json={"name": "test", "price": 25.50})
        data = r.json()
        assert "price" in data
        assert data["price"] == 25.50

    def test_create_item_response_no_extra_fields(self):
        """Test that response only has expected fields."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        expected_keys = {"id", "name", "price"}
        assert set(data.keys()) == expected_keys


class TestGetItemResponseFields:
    """Test response field presence and types for get_item."""

    def test_get_item_response_has_id(self):
        """Test that response includes id field."""
        r = client.get("/items/1")
        data = r.json()
        assert "id" in data
        assert data["id"] == 1

    def test_get_item_response_has_name(self):
        """Test that response includes name field."""
        r = client.get("/items/1")
        data = r.json()
        assert "name" in data
        assert isinstance(data["name"], str)

    def test_get_item_response_has_price(self):
        """Test that response includes price field."""
        r = client.get("/items/1")
        data = r.json()
        assert "price" in data
        assert isinstance(data["price"], (int, float))

    def test_get_item_response_no_extra_fields(self):
        """Test that response only has expected fields."""
        r = client.get("/items/1")
        data = r.json()
        expected_keys = {"id", "name", "price"}
        assert set(data.keys()) == expected_keys


class TestErrorResponseStructure:
    """Test error response structure and content."""

    def test_create_item_invalid_price_error_detail(self):
        """Test that invalid price error has proper detail message."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data
        assert data["detail"] == "price must be > 0"

    def test_get_item_not_found_error_detail(self):
        """Test that not found error has proper detail message."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert data["detail"] == "not found"

    def test_create_item_missing_field_error_has_detail(self):
        """Test that missing field errors have detail."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_create_item_invalid_type_error_has_detail(self):
        """Test that type validation errors have detail."""
        r = client.post("/items", json={"name": "test", "price": "invalid"})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data


class TestResponseValueTypes:
    """Test that response values have correct types."""

    def test_create_item_id_is_integer(self):
        """Test that id in response is an integer."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        assert isinstance(data["id"], int)
        assert not isinstance(data["id"], bool)

    def test_create_item_name_is_string(self):
        """Test that name in response is a string."""
        r = client.post("/items", json={"name": "product", "price": 10.0})
        data = r.json()
        assert isinstance(data["name"], str)

    def test_create_item_price_is_number(self):
        """Test that price in response is a number (int or float)."""
        r = client.post("/items", json={"name": "test", "price": 10.5})
        data = r.json()
        assert isinstance(data["price"], (int, float))
        assert not isinstance(data["price"], bool)

    def test_get_item_id_is_integer(self):
        """Test that id in get response is an integer."""
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data["id"], int)

    def test_get_item_name_is_string(self):
        """Test that name in get response is a string."""
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data["name"], str)

    def test_get_item_price_is_number(self):
        """Test that price in get response is a number."""
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data["price"], (int, float))


class TestResponseDataConsistency:
    """Test consistency of response data."""

    def test_create_item_echoes_input_name(self):
        """Test that response name matches input."""
        input_name = "TestProduct"
        r = client.post("/items", json={"name": input_name, "price": 10.0})
        data = r.json()
        assert data["name"] == input_name

    def test_create_item_echoes_input_price(self):
        """Test that response price matches input."""
        input_price = 19.99
        r = client.post("/items", json={"name": "test", "price": input_price})
        data = r.json()
        assert data["price"] == input_price

    def test_create_item_id_is_one(self):
        """Test that created item always has id=1 (mocked behavior)."""
        r1 = client.post("/items", json={"name": "item1", "price": 10.0})
        r2 = client.post("/items", json={"name": "item2", "price": 20.0})
        # Both calls return id=1 (stateless mock implementation)
        assert r1.json()["id"] == 1
        assert r2.json()["id"] == 1

    def test_get_item_one_returns_fixed_data(self):
        """Test that get_item/1 returns fixed mock data."""
        r = client.get("/items/1")
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_endpoint_exists(self):
        """Test that health endpoint is accessible."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_endpoint_returns_status(self):
        """Test that health endpoint returns status field."""
        r = client.get("/health")
        data = r.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_health_endpoint_json_format(self):
        """Test that health endpoint returns JSON."""
        r = client.get("/health")
        assert "application/json" in r.headers.get("content-type", "")
        data = r.json()
        assert isinstance(data, dict)
