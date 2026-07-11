from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


@pytest.fixture
def sample_item_data():
    """Fixture providing sample item data."""
    return {"name": "test_item", "price": 25.50}


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_ok(self):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_returns_status_field(self):
        r = client.get("/health")
        data = r.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_health_response_type(self):
        r = client.get("/health")
        assert r.headers["content-type"] == "application/json"


class TestParametrizedIntegration:
    """Parametrized integration tests for various scenarios."""

    @pytest.mark.parametrize("price", [0.01, 1.0, 99.99, 500.0])
    def test_create_item_various_prices(self, price):
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize(
        "name,price",
        [
            ("apple", 1.5),
            ("book", 12.99),
            ("laptop", 999.99),
            ("item with spaces", 10.0),
        ],
    )
    def test_create_item_various_data(self, name, price):
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price


class TestResponseValidation:
    """Test response structure and validation."""

    def test_create_item_response_contains_all_fields(self, sample_item_data):
        r = client.post("/items", json=sample_item_data)
        assert r.status_code == 200
        data = r.json()
        required_fields = ["id", "name", "price"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_get_item_response_complete(self):
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        required_fields = ["id", "name", "price"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_error_response_structure(self):
        r = client.post("/items", json={"name": "test", "price": -1})
        assert r.status_code == 400
        error_data = r.json()
        assert "detail" in error_data

    def test_validation_error_response_structure(self):
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        error_data = r.json()
        assert "detail" in error_data


class TestStatusCodes:
    """Test correct HTTP status codes."""

    def test_health_returns_200(self):
        r = client.get("/health")
        assert r.status_code == 200

    def test_create_item_success_returns_200(self):
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200

    def test_create_item_validation_error_returns_422(self):
        r = client.post("/items", json={"name": "test", "price": "invalid"})
        assert r.status_code == 422

    def test_create_item_business_logic_error_returns_400(self):
        r = client.post("/items", json={"name": "test", "price": -1})
        assert r.status_code == 400

    def test_get_item_found_returns_200(self):
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_not_found_returns_404(self):
        r = client.get("/items/999")
        assert r.status_code == 404


class TestDataTypeConsistency:
    """Test data type consistency in responses."""

    def test_item_id_is_integer(self):
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        assert isinstance(data["id"], int)

    def test_item_name_is_string(self):
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        assert isinstance(data["name"], str)

    def test_item_price_is_number(self):
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        assert isinstance(data["price"], (int, float))

    def test_get_item_id_is_integer(self):
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data["id"], int)

    def test_get_item_price_is_number(self):
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data["price"], (int, float))


class TestStressScenarios:
    """Test stress scenarios and boundary conditions."""

    def test_create_multiple_items_sequentially(self):
        for i in range(5):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200

    def test_get_nonexistent_item_repeatedly(self):
        for i in range(5):
            r = client.get(f"/items/{1000 + i}")
            assert r.status_code == 404

    def test_create_item_with_max_price(self):
        max_price = 1e308
        r = client.post("/items", json={"name": "expensive", "price": max_price})
        assert r.status_code == 200
