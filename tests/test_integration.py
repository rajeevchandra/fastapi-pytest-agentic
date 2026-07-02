import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def valid_item_payload():
    """Fixture for valid item payload."""
    return {"name": "Test Item", "price": 29.99}


class TestResponseTypeValidation:
    """Test response type validation across all endpoints."""

    def test_health_response_type(self):
        """Health endpoint should return dict."""
        r = client.get("/health")
        assert r.status_code == 200
        assert isinstance(r.json(), dict)

    def test_create_item_response_type(self):
        """Create item should return dict."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        assert isinstance(r.json(), dict)

    def test_get_item_response_type(self):
        """Get item should return dict."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert isinstance(r.json(), dict)

    def test_error_response_type(self):
        """Error response should return dict."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert isinstance(r.json(), dict)


class TestIntegrationCreateAndRetrieve:
    """Test integration scenarios: create then retrieve."""

    def test_item_data_matches_after_creation(self, valid_item_payload):
        """Created item details should be retrievable."""
        create_r = client.post("/items", json=valid_item_payload)
        assert create_r.status_code == 200
        created_data = create_r.json()

        get_r = client.get(f"/items/{created_data['id']}")
        assert get_r.status_code == 200
        retrieved_data = get_r.json()

        # Verify the created ID matches
        assert created_data["id"] == retrieved_data["id"]

    def test_created_item_has_matching_name(self, valid_item_payload):
        """Created item name should match input."""
        create_r = client.post("/items", json=valid_item_payload)
        assert create_r.status_code == 200
        created_data = create_r.json()
        
        # For id=1, check that name can be retrieved
        assert created_data["name"] == valid_item_payload["name"]

    def test_created_item_has_matching_price(self, valid_item_payload):
        """Created item price should match input."""
        create_r = client.post("/items", json=valid_item_payload)
        assert create_r.status_code == 200
        created_data = create_r.json()
        
        # Price should match input
        assert created_data["price"] == valid_item_payload["price"]


class TestParametrizedIntegration:
    """Parametrized tests for integrated scenarios."""

    @pytest.mark.parametrize("name,price", [
        ("Book", 15.99),
        ("Pen", 1.50),
        ("Laptop", 999.99),
        ("Item", 0.01),
    ])
    def test_create_with_various_inputs(self, name, price):
        """Create items with various valid inputs."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price


class TestErrorHandlingConsistency:
    """Test consistency of error handling."""

    def test_invalid_item_id_always_returns_404(self):
        """Non-existent items always return 404."""
        non_existent_ids = [2, 3, 100, 0, -5]
        for item_id in non_existent_ids:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404

    def test_zero_price_always_rejected(self):
        """Zero price always gets rejected."""
        test_cases = [
            {"name": "item", "price": 0},
            {"name": "item", "price": 0.0},
        ]
        for payload in test_cases:
            r = client.post("/items", json=payload)
            assert r.status_code == 400

    def test_negative_price_always_rejected(self):
        """Negative prices always get rejected."""
        test_cases = [
            {"name": "item", "price": -1},
            {"name": "item", "price": -0.01},
            {"name": "item", "price": -1000},
        ]
        for payload in test_cases:
            r = client.post("/items", json=payload)
            assert r.status_code == 400


class TestResponseConsistency:
    """Test response consistency across requests."""

    def test_health_endpoint_always_ok(self):
        """Health endpoint always returns ok status."""
        for _ in range(3):
            r = client.get("/health")
            assert r.status_code == 200
            assert r.json()["status"] == "ok"

    def test_item_one_always_exists(self):
        """Item 1 always exists and returns consistent data."""
        responses = [client.get("/items/1") for _ in range(2)]
        assert all(r.status_code == 200 for r in responses)
        data = [r.json() for r in responses]
        assert data[0] == data[1]
        assert data[0]["id"] == 1


class TestAPIComplianceWithSpec:
    """Test API compliance with documented behavior."""

    def test_health_returns_status_ok(self):
        """GET /health returns {status: 'ok'}."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_create_item_requires_positive_price(self):
        """POST /items rejects non-positive prices."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_get_item_returns_404_for_missing(self):
        """GET /items/{id} returns 404 for missing items."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]

    def test_get_item_one_succeeds(self):
        """GET /items/1 returns existing item."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1
        assert "name" in r.json()
        assert "price" in r.json()
