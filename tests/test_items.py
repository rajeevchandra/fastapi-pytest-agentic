from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


def test_create_item_success():
    r = client.post("/items", json={"name": "book", "price": 12.5})
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == 1
    assert data["name"] == "book"
    assert data["price"] == 12.5


def test_create_item_rejects_non_positive_price():
    r = client.post("/items", json={"name": "bad", "price": 0})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


def test_get_item_found():
    r = client.get("/items/1")
    assert r.status_code == 200
    assert r.json()["id"] == 1


def test_get_item_not_found():
    r = client.get("/items/2")
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"


# PR #3: Integration & Response Validation Tests

# Fixtures for reusable test setup
@pytest.fixture
def valid_item_payload():
    """Fixture providing valid item creation payload."""
    return {"name": "test_item", "price": 29.99}


@pytest.fixture
def error_response_structure():
    """Fixture defining expected error response structure."""
    def check(response):
        assert "detail" in response
        assert isinstance(response["detail"], str)
    return check


class TestCreateItemResponseValidation:
    """Test response structure and validation for POST /items."""

    def test_response_has_all_required_fields(self, valid_item_payload):
        """Created item response should have id, name, and price."""
        r = client.post("/items", json=valid_item_payload)
        assert r.status_code == 200
        data = r.json()
        required_fields = {"id", "name", "price"}
        assert required_fields.issubset(data.keys())

    def test_response_contains_no_extra_fields(self, valid_item_payload):
        """Response should contain exactly id, name, price."""
        r = client.post("/items", json=valid_item_payload)
        assert r.status_code == 200
        data = r.json()
        expected_fields = {"id", "name", "price"}
        assert set(data.keys()) == expected_fields

    def test_response_id_is_always_one(self, valid_item_payload):
        """ID in response should always be 1."""
        r = client.post("/items", json=valid_item_payload)
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_response_preserves_item_name(self, valid_item_payload):
        """Response name should match request name."""
        r = client.post("/items", json=valid_item_payload)
        assert r.status_code == 200
        assert r.json()["name"] == valid_item_payload["name"]

    def test_response_preserves_item_price(self, valid_item_payload):
        """Response price should match request price."""
        r = client.post("/items", json=valid_item_payload)
        assert r.status_code == 200
        assert r.json()["price"] == valid_item_payload["price"]

    def test_content_type_is_json(self, valid_item_payload):
        """Response content-type should be application/json."""
        r = client.post("/items", json=valid_item_payload)
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")


class TestErrorResponseValidation:
    """Test error response structure and consistency."""

    def test_negative_price_error_structure(self, error_response_structure):
        """Error response for negative price should have detail field."""
        r = client.post("/items", json={"name": "item", "price": -5})
        assert r.status_code == 400
        error_response_structure(r.json())

    def test_not_found_error_structure(self, error_response_structure):
        """404 response should have detail field."""
        r = client.get("/items/999")
        assert r.status_code == 404
        error_response_structure(r.json())

    def test_validation_error_response_code(self):
        """Missing required fields should return 422."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422

    def test_validation_error_response_has_detail(self):
        """422 validation error should include detail."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422
        assert "detail" in r.json()


class TestIntegrationScenarios:
    """Test realistic API usage scenarios."""

    def test_create_and_retrieve_flow(self):
        """Should be able to create item then retrieve it."""
        create_r = client.post("/items", json={"name": "integration_test", "price": 50.0})
        assert create_r.status_code == 200
        
        get_r = client.get("/items/1")
        assert get_r.status_code == 200
        assert get_r.json()["id"] == 1

    def test_multiple_get_requests_consistency(self):
        """Multiple GET requests for same item should return consistent data."""
        responses = [client.get("/items/1") for _ in range(3)]
        
        assert all(r.status_code == 200 for r in responses)
        data_set = [r.json() for r in responses]
        
        assert all(d["id"] == 1 for d in data_set)
        assert all(d["name"] == "sample" for d in data_set)
        assert all(d["price"] == 10.0 for d in data_set)

    def test_not_found_consistency(self):
        """Multiple GET requests for non-existent item should be consistent."""
        responses = [client.get("/items/999") for _ in range(3)]
        
        assert all(r.status_code == 404 for r in responses)
        assert all(r.json()["detail"] == "not found" for r in responses)


class TestParametrizedPriceValidation:
    """Parametrized tests for various price values."""

    @pytest.mark.parametrize("price", [0.01, 1, 10, 100, 999.99])
    def test_accepts_positive_prices(self, price):
        """Should accept all positive prices."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [0, -0.01, -1, -100])
    def test_rejects_non_positive_prices(self, price):
        """Should reject zero and negative prices."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]


class TestParametrizedItemIds:
    """Parametrized tests for various item IDs."""

    @pytest.mark.parametrize("item_id", [2, 3, 10, 100, 999])
    def test_non_existent_ids_return_404(self, item_id):
        """Non-existent item IDs should return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_valid_id_returns_200(self):
        """Valid item ID (1) should return 200."""
        r = client.get("/items/1")
        assert r.status_code == 200


class TestHealthEndpoint:
    """Tests for the health endpoint."""

    def test_health_endpoint_exists(self):
        """Health endpoint should be accessible."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_response_structure(self):
        """Health response should have status field."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_health_response_format(self):
        """Health response should be valid JSON with correct content type."""
        r = client.get("/health")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")
