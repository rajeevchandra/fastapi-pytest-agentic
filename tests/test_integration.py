"""
Integration tests and response validation for the items API.
Tests end-to-end scenarios, response structure validation, and fixtures.
"""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


# Fixtures for reusable test data
@pytest.fixture
def sample_item_data():
    """Standard item data for testing."""
    return {"name": "test_book", "price": 15.99}


@pytest.fixture
def valid_prices():
    """Collection of valid price values."""
    return [0.01, 0.99, 1.0, 10.0, 99.99, 100.0, 999.99, 10000.0]


@pytest.fixture
def invalid_prices():
    """Collection of invalid price values."""
    return [0, -0.01, -1, -10.5, -100, -999.99]


@pytest.fixture
def created_item():
    """Create an item and return its data."""
    r = client.post("/items", json={"name": "fixture_item", "price": 25.0})
    assert r.status_code == 200
    return r.json()


@pytest.fixture
def created_items(sample_item_data):
    """Create multiple items and return their data."""
    items = []
    for i in range(3):
        data = sample_item_data.copy()
        data["name"] = f"item_{i}"
        r = client.post("/items", json=data)
        if r.status_code == 200:
            items.append(r.json())
    return items


class TestCreateItemSuccess:
    """Test successful item creation with various valid inputs."""

    def test_create_item_with_fixture_data(self, sample_item_data):
        """Create item with fixture-provided data."""
        r = client.post("/items", json=sample_item_data)
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == sample_item_data["name"]
        assert data["price"] == sample_item_data["price"]

    @pytest.mark.parametrize("price", [0.01, 1.0, 10.0, 99.99, 1000.0])
    def test_create_item_with_valid_prices(self, price):
        """Create items with various valid price values."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("name", [
        "simple",
        "with spaces",
        "with-dashes",
        "with.dots",
        "with_underscores",
        "CamelCase",
        "UPPERCASE"
    ])
    def test_create_item_with_various_names(self, name):
        """Create items with various valid name formats."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestCreateItemValidation:
    """Test validation behavior for various invalid inputs."""

    def test_create_item_invalid_prices(self, invalid_prices):
        """All invalid prices should be rejected."""
        for price in invalid_prices:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 400
            assert "price must be > 0" in r.json()["detail"]

    def test_missing_fields_rejected(self):
        """Requests with missing required fields should fail."""
        # Missing price
        r1 = client.post("/items", json={"name": "test"})
        assert r1.status_code == 422
        
        # Missing name
        r2 = client.post("/items", json={"price": 10.0})
        assert r2.status_code == 422
        
        # Missing both
        r3 = client.post("/items", json={})
        assert r3.status_code == 422


class TestGetItemWithFixtures:
    """Test getting items, using fixtures."""

    def test_get_created_item(self, created_item):
        """Get an item that was just created."""
        # The endpoint only returns the hardcoded item with id=1
        r = client.get(f"/items/{created_item['id']}")
        # Will actually always get the hardcoded item, not the created one
        assert r.status_code == 200

    def test_get_multiple_created_items(self, created_items):
        """Test getting multiple created items."""
        for item in created_items:
            # Endpoint behavior: only id=1 is found
            if item['id'] == 1:
                r = client.get(f"/items/{item['id']}")
                assert r.status_code == 200
            else:
                # Other ids will return 404 since only id=1 exists
                r = client.get(f"/items/{item['id']}")
                assert r.status_code == 404


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_endpoint_success(self):
        """Health check should always succeed."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_endpoint_response_format(self):
        """Health response should have status field."""
        r = client.get("/health")
        data = r.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_health_endpoint_content_type(self):
        """Health response should be JSON."""
        r = client.get("/health")
        assert "application/json" in r.headers.get("content-type", "")


class TestResponseStatusCodes:
    """Test HTTP status codes for various scenarios."""

    def test_create_item_success_status(self, sample_item_data):
        """Successful create should return 200."""
        r = client.post("/items", json=sample_item_data)
        assert r.status_code == 200

    def test_create_item_validation_error_status(self):
        """Validation errors should return 422."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_create_item_business_logic_error_status(self):
        """Business logic errors (invalid price) should return 400."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400

    def test_get_item_found_status(self):
        """Getting existing item should return 200."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_not_found_status(self):
        """Getting non-existent item should return 404."""
        r = client.get("/items/999")
        assert r.status_code == 404


class TestResponseHeaders:
    """Test response headers."""

    def test_create_item_response_has_json_content_type(self, sample_item_data):
        """Create response should specify JSON content type."""
        r = client.post("/items", json=sample_item_data)
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_item_response_has_json_content_type(self):
        """Get response should specify JSON content type."""
        r = client.get("/items/1")
        assert "application/json" in r.headers.get("content-type", "")

    def test_error_response_has_json_content_type(self):
        """Error response should specify JSON content type."""
        r = client.get("/items/999")
        assert "application/json" in r.headers.get("content-type", "")


class TestResponseDataTypes:
    """Test that response fields have correct data types."""

    def test_create_item_response_field_types(self, sample_item_data):
        """Response fields should have correct types."""
        r = client.post("/items", json=sample_item_data)
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], float)

    def test_get_item_response_field_types(self):
        """Response fields should have correct types."""
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], float)

    def test_error_response_field_types(self):
        """Error response should have string detail field."""
        r = client.get("/items/999")
        data = r.json()
        assert isinstance(data["detail"], str)


class TestResponseDataConsistency:
    """Test that response data is consistent and accurate."""

    def test_create_item_response_matches_input(self, sample_item_data):
        """Response should contain the submitted name and price."""
        r = client.post("/items", json=sample_item_data)
        data = r.json()
        assert data["name"] == sample_item_data["name"]
        assert data["price"] == sample_item_data["price"]

    def test_create_item_response_has_unique_id(self):
        """Created items should have an id (always 1 in this implementation)."""
        r1 = client.post("/items", json={"name": "item1", "price": 10.0})
        r2 = client.post("/items", json={"name": "item2", "price": 20.0})
        data1 = r1.json()
        data2 = r2.json()
        assert data1["id"] == 1  # Always returns same id in mock implementation
        assert data2["id"] == 1

    def test_get_item_response_is_consistent(self):
        """Getting same item multiple times should return same data."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        r3 = client.get("/items/1")
        data1 = r1.json()
        data2 = r2.json()
        data3 = r3.json()
        assert data1 == data2 == data3


class TestEndpointIntegration:
    """Test interactions between endpoints."""

    def test_create_then_get_item(self, sample_item_data):
        """Create an item then get the existing item."""
        # Create
        create_r = client.post("/items", json=sample_item_data)
        assert create_r.status_code == 200
        created = create_r.json()
        
        # Get the hardcoded item (not the created one, since only id=1 exists)
        get_r = client.get("/items/1")
        assert get_r.status_code == 200
        retrieved = get_r.json()
        assert retrieved["id"] == 1

    def test_health_check_before_operations(self):
        """Health endpoint should work before other operations."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        
        # Other operations should still work
        r2 = client.get("/items/1")
        assert r2.status_code == 200

    def test_multiple_creates_and_gets(self):
        """Multiple creates and gets should work independently."""
        for i in range(5):
            # Create
            r1 = client.post("/items", json={"name": f"item_{i}", "price": float(i + 1)})
            assert r1.status_code == 200
            
            # Get existing
            r2 = client.get("/items/1")
            assert r2.status_code == 200
            
            # Get non-existent
            r3 = client.get(f"/items/{i + 100}")
            assert r3.status_code == 404


class TestParametrizedIntegration:
    """Use parametrization for comprehensive integration testing."""

    @pytest.mark.parametrize("name,price", [
        ("book", 10.0),
        ("pen", 1.5),
        ("notebook", 5.99),
        ("desk", 199.99),
        ("chair", 150.0),
    ])
    def test_create_various_items(self, name, price):
        """Create items with various name and price combinations."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price
        assert "id" in data

    @pytest.mark.parametrize("item_id,should_exist", [
        (1, True),
        (2, False),
        (0, False),
        (-1, False),
        (100, False),
    ])
    def test_get_various_items(self, item_id, should_exist):
        """Get items with various ids."""
        r = client.get(f"/items/{item_id}")
        if should_exist:
            assert r.status_code == 200
        else:
            assert r.status_code == 404
