"""
Integration tests and advanced test organization using fixtures.
Tests end-to-end API workflows and complete response validation.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# Fixtures for test organization and reusability
@pytest.fixture
def valid_item_payload():
    """Standard valid item payload for testing"""
    return {"name": "test_item", "price": 19.99}


@pytest.fixture
def valid_item_data():
    """Standard valid item data with known values"""
    return {"id": 1, "name": "sample", "price": 10.0}


@pytest.fixture
def client_fixture():
    """Provide test client fixture"""
    return client


class TestHealthEndpoint:
    """Health check endpoint tests"""
    
    def test_health_returns_ok_status(self):
        """Health endpoint should return ok status"""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_health_response_contains_status_field(self):
        """Health response must contain status field"""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data

    def test_health_endpoint_is_json(self):
        """Health endpoint returns JSON"""
        r = client.get("/health")
        assert "application/json" in r.headers.get("content-type", "")


class TestResponseStructureValidation:
    """Comprehensive response structure validation"""
    
    def test_create_item_response_has_required_fields(self, valid_item_payload):
        """Response should have id, name, and price fields"""
        r = client.post("/items", json=valid_item_payload)
        assert r.status_code == 200
        data = r.json()
        required_fields = {"id", "name", "price"}
        assert required_fields.issubset(data.keys())

    def test_create_item_response_no_extra_fields(self, valid_item_payload):
        """Response should only have id, name, and price"""
        r = client.post("/items", json=valid_item_payload)
        assert r.status_code == 200
        data = r.json()
        assert set(data.keys()) == {"id", "name", "price"}

    def test_get_item_response_has_required_fields(self, valid_item_data):
        """GET response should have id, name, and price fields"""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        required_fields = {"id", "name", "price"}
        assert required_fields.issubset(data.keys())

    def test_get_item_response_no_extra_fields(self, valid_item_data):
        """GET response should only have id, name, and price"""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert set(data.keys()) == {"id", "name", "price"}

    def test_error_response_has_detail_field(self):
        """Error responses should have detail field"""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data


class TestCreateItemIntegration:
    """Integration tests for create item workflow"""
    
    def test_create_item_successful_response_has_correct_id(self, valid_item_payload):
        """Created item should have id field"""
        r = client.post("/items", json=valid_item_payload)
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert isinstance(data["id"], int)
        assert data["id"] > 0

    def test_create_item_successful_response_echoes_name(self, valid_item_payload):
        """Response should echo the provided name"""
        test_name = "special_item_name"
        payload = {"name": test_name, "price": 25.50}
        r = client.post("/items", json=payload)
        assert r.status_code == 200
        assert r.json()["name"] == test_name

    def test_create_item_successful_response_echoes_price(self, valid_item_payload):
        """Response should echo the provided price"""
        test_price = 42.99
        payload = {"name": "item", "price": test_price}
        r = client.post("/items", json=payload)
        assert r.status_code == 200
        assert r.json()["price"] == test_price

    def test_create_and_retrieve_item_workflow(self):
        """Complete workflow: create item, then retrieve it"""
        # Create item
        create_r = client.post("/items", json={"name": "workflow_test", "price": 15.00})
        assert create_r.status_code == 200
        created_item = create_r.json()
        
        # Retrieve item
        get_r = client.get(f"/items/{created_item['id']}")
        assert get_r.status_code == 200
        retrieved_item = get_r.json()
        
        # Verify retrieval (id should match)
        assert retrieved_item["id"] == created_item["id"]


class TestErrorHandlingIntegration:
    """Integration tests for error handling"""
    
    def test_error_response_format_for_validation_error(self):
        """Validation errors should have proper format"""
        r = client.post("/items", json={"name": "item"})  # missing price
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_error_response_format_for_business_logic_error(self):
        """Business logic errors should have proper format"""
        r = client.post("/items", json={"name": "item", "price": -5})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data
        assert "price" in data["detail"].lower()

    def test_error_response_format_for_not_found(self):
        """Not found errors should have proper format"""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data


class TestParametrizedIntegration:
    """Parametrized integration tests for comprehensive coverage"""
    
    @pytest.mark.parametrize("name,price", [
        ("item1", 10.00),
        ("item2", 20.50),
        ("item3", 1.99),
        ("item4", 999.99),
        ("unicode_商品", 15.00),
    ])
    def test_create_item_various_valid_inputs(self, name, price):
        """Test create with various valid inputs"""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price

    @pytest.mark.parametrize("invalid_price", [0, -1, -10.50])
    def test_create_item_rejects_invalid_prices(self, invalid_price):
        """Test that various invalid prices are rejected"""
        r = client.post("/items", json={"name": "item", "price": invalid_price})
        assert r.status_code == 400
        assert "price" in r.json()["detail"].lower()

    @pytest.mark.parametrize("item_id", [1, 2, 100, -1, 0])
    def test_get_item_various_ids(self, item_id):
        """Test GET with various item IDs"""
        r = client.get(f"/items/{item_id}")
        if item_id == 1:
            assert r.status_code == 200
        else:
            assert r.status_code == 404


class TestHeaderValidation:
    """Test HTTP headers in responses"""
    
    def test_successful_post_response_has_content_type(self):
        """POST response should have content-type header"""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert "content-type" in r.headers
        assert "application/json" in r.headers["content-type"]

    def test_successful_get_response_has_content_type(self):
        """GET response should have content-type header"""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "content-type" in r.headers
        assert "application/json" in r.headers["content-type"]

    def test_error_response_has_content_type(self):
        """Error response should have content-type header"""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "content-type" in r.headers
        assert "application/json" in r.headers["content-type"]


class TestResponseConsistency:
    """Test consistency of API responses"""
    
    def test_create_item_always_returns_dict(self):
        """Create item should always return a dictionary"""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert isinstance(r.json(), dict)

    def test_get_item_found_always_returns_dict(self):
        """GET found should always return a dictionary"""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert isinstance(r.json(), dict)

    def test_error_response_always_has_detail(self):
        """All error responses should have detail field"""
        error_responses = [
            client.get("/items/999"),  # 404
            client.post("/items", json={"name": "item"}),  # 422
            client.post("/items", json={"name": "item", "price": -1}),  # 400
        ]
        for r in error_responses:
            assert r.status_code >= 400
            assert "detail" in r.json()


class TestDataTypeValidation:
    """Validate data types in responses"""
    
    def test_create_item_response_id_is_integer(self):
        """ID should be an integer"""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert isinstance(r.json()["id"], int)

    def test_create_item_response_name_is_string(self):
        """Name should be a string"""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert isinstance(r.json()["name"], str)

    def test_create_item_response_price_is_number(self):
        """Price should be a number (int or float)"""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert isinstance(r.json()["price"], (int, float))

    def test_get_item_response_id_is_integer(self):
        """ID should be an integer"""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert isinstance(r.json()["id"], int)

    def test_get_item_response_name_is_string(self):
        """Name should be a string"""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert isinstance(r.json()["name"], str)

    def test_get_item_response_price_is_number(self):
        """Price should be a number"""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert isinstance(r.json()["price"], (int, float))


class TestBusinessLogicValidation:
    """Test API business logic"""
    
    def test_created_item_id_is_always_one(self):
        """Created item always gets id=1"""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_created_item_has_positive_id(self):
        """Created item ID should be positive"""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["id"] > 0

    def test_created_item_price_matches_request(self):
        """Created item price should match request price"""
        test_price = 42.50
        r = client.post("/items", json={"name": "item", "price": test_price})
        assert r.status_code == 200
        assert r.json()["price"] == test_price

    def test_created_item_name_matches_request(self):
        """Created item name should match request name"""
        test_name = "specific_name_test"
        r = client.post("/items", json={"name": test_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == test_name

    def test_get_item_one_has_fixed_values(self):
        """Item 1 should have fixed known values"""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0
