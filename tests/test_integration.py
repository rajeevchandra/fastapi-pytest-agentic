from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


@pytest.fixture
def client_fixture():
    """Provide TestClient fixture for integration tests"""
    return TestClient(app)


class TestResponseStructureValidation:
    """Test complete response structure and field validation"""

    def test_create_item_response_has_all_fields(self):
        """Test create response contains all required fields"""
        r = client.post("/items", json={"name": "book", "price": 15.99})
        assert r.status_code == 200
        data = r.json()
        assert all(field in data for field in ["id", "name", "price"])

    def test_create_item_response_no_extra_fields(self):
        """Test create response contains only expected fields"""
        r = client.post("/items", json={"name": "book", "price": 15.99})
        assert r.status_code == 200
        data = r.json()
        assert set(data.keys()) == {"id", "name", "price"}

    def test_create_item_extra_request_fields_ignored(self):
        """Test that extra fields in request are ignored"""
        r = client.post("/items", json={
            "name": "book",
            "price": 15.99,
            "extra_field": "should_be_ignored",
            "another_field": 123
        })
        assert r.status_code == 200
        data = r.json()
        assert "extra_field" not in data
        assert "another_field" not in data

    def test_get_item_response_matches_create(self):
        """Test GET response has same structure as POST response"""
        post_r = client.post("/items", json={"name": "test", "price": 20.0})
        get_r = client.get("/items/1")
        
        assert post_r.status_code == 200
        assert get_r.status_code == 200
        
        post_keys = set(post_r.json().keys())
        get_keys = set(get_r.json().keys())
        assert post_keys == get_keys


class TestResponseFieldValidation:
    """Test individual response field values and types"""

    def test_create_item_id_always_one(self):
        """Test that created item always has id=1"""
        for _ in range(3):
            r = client.post("/items", json={"name": "item", "price": 10.0})
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_create_item_name_preserved(self):
        """Test that item name is preserved in response"""
        names = ["book", "pen", "notebook", ""]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name

    def test_create_item_price_preserved(self):
        """Test that item price is preserved in response"""
        prices = [0.01, 1.0, 10.5, 999.99]
        for price in prices:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price

    def test_get_item_price_type_is_float(self):
        """Test that GET response price is float type"""
        r = client.get("/items/1")
        assert r.status_code == 200
        price = r.json()["price"]
        assert isinstance(price, (int, float))


class TestErrorResponseStructure:
    """Test error response structures across different status codes"""

    def test_error_400_has_detail_field(self):
        """Test 400 error has detail field"""
        r = client.post("/items", json={"name": "item", "price": -1})
        assert r.status_code == 400
        assert "detail" in r.json()
        assert isinstance(r.json()["detail"], str)

    def test_error_404_has_detail_field(self):
        """Test 404 error has detail field"""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "detail" in r.json()
        assert isinstance(r.json()["detail"], str)

    def test_error_422_has_detail_field(self):
        """Test 422 validation error has detail field"""
        r = client.post("/items", json={"name": "item"})  # missing price
        assert r.status_code == 422
        assert "detail" in r.json()


class TestIntegrationScenarios:
    """Test realistic end-to-end integration scenarios"""

    def test_create_and_retrieve_item(self):
        """Test creating an item and then retrieving it"""
        # Create item
        create_r = client.post("/items", json={"name": "laptop", "price": 999.99})
        assert create_r.status_code == 200
        created = create_r.json()
        
        # Retrieve item
        get_r = client.get(f"/items/{created['id']}")
        assert get_r.status_code == 200
        retrieved = get_r.json()
        
        # Verify data consistency
        assert retrieved["name"] == created["name"]
        assert retrieved["price"] == created["price"]

    def test_create_with_decimal_price_retrieve(self):
        """Test creating item with decimal price and retrieving"""
        create_r = client.post("/items", json={"name": "item", "price": 12.34})
        assert create_r.status_code == 200
        
        get_r = client.get("/items/1")
        assert get_r.status_code == 200
        assert get_r.json()["price"] == 12.34

    def test_multiple_create_attempts_with_invalid_then_valid(self):
        """Test sequence of invalid then valid requests"""
        # Invalid: negative price
        r1 = client.post("/items", json={"name": "item", "price": -10})
        assert r1.status_code == 400
        
        # Invalid: missing field
        r2 = client.post("/items", json={"name": "item"})
        assert r2.status_code == 422
        
        # Valid
        r3 = client.post("/items", json={"name": "item", "price": 10})
        assert r3.status_code == 200
        assert r3.json()["name"] == "item"

    def test_retrieve_nonexistent_after_valid_create(self):
        """Test that nonexistent items return 404 even after creating valid items"""
        # Create valid item
        r1 = client.post("/items", json={"name": "item", "price": 10})
        assert r1.status_code == 200
        
        # Try to retrieve different item
        r2 = client.get("/items/2")
        assert r2.status_code == 404
        
        # Retrieve valid item again
        r3 = client.get("/items/1")
        assert r3.status_code == 200


@pytest.mark.parametrize("name,price,expected_status", [
    ("book", 10.0, 200),
    ("pen", 0.5, 200),
    ("", 5.0, 200),
    ("item", 0, 400),
    ("item", -1, 400),
    ("item", -100, 400),
])
def test_create_item_parametrized_scenarios(name, price, expected_status):
    """Parametrized integration test for create_item with various inputs"""
    r = client.post("/items", json={"name": name, "price": price})
    assert r.status_code == expected_status


@pytest.mark.parametrize("item_id,expected_status", [
    (1, 200),
    (0, 404),
    (-1, 404),
    (2, 404),
    (999, 404),
    (9999, 404),
])
def test_get_item_parametrized_scenarios(item_id, expected_status):
    """Parametrized integration test for get_item with various IDs"""
    r = client.get(f"/items/{item_id}")
    assert r.status_code == expected_status


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_status_field(self):
        """Test health response has status field"""
        r = client.get("/health")
        assert r.status_code == 200
        assert "status" in r.json()

    def test_health_status_value(self):
        """Test health returns correct status"""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_response_type(self):
        """Test health response is valid JSON"""
        r = client.get("/health")
        assert r.status_code == 200
        assert isinstance(r.json(), dict)


class TestHeaderValidation:
    """Test response headers across endpoints"""

    def test_all_endpoints_return_json_content_type(self):
        """Test all endpoints return JSON content type"""
        endpoints = [
            ("GET", "/health"),
            ("GET", "/items/1"),
            ("POST", "/items", {"name": "item", "price": 10}),
        ]
        
        for method, path, *data in endpoints:
            if method == "GET":
                r = client.get(path)
            else:
                r = client.post(path, json=data[0] if data else {})
            
            content_type = r.headers.get("content-type", "")
            assert "application/json" in content_type
