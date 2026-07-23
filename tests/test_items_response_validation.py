import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemResponseStructure:
    """Tests for POST /items response structure and data types."""

    def test_create_item_response_contains_id(self):
        """Verify response contains id field."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert "id" in r.json()
        assert isinstance(r.json()["id"], int)

    def test_create_item_response_contains_name(self):
        """Verify response contains name field."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert "name" in r.json()
        assert isinstance(r.json()["name"], str)

    def test_create_item_response_contains_price(self):
        """Verify response contains price field."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert "price" in r.json()
        assert isinstance(r.json()["price"], (int, float))

    def test_create_item_response_has_exactly_three_fields(self):
        """Verify response contains exactly id, name, and price."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        data = r.json()
        assert set(data.keys()) == {"id", "name", "price"}

    def test_create_item_response_fields_match_input(self):
        """Verify response echoes back input values correctly."""
        name = "book"
        price = 12.5
        r = client.post("/items", json={"name": name, "price": price})
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price


class TestErrorResponseStructure:
    """Tests for error response consistency and format."""

    def test_error_response_has_detail_field(self):
        """Verify error responses include detail field."""
        r = client.post("/items", json={"name": "item", "price": -1})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data

    def test_error_response_detail_is_string(self):
        """Verify detail field is a string."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert isinstance(r.json()["detail"], str)

    def test_validation_error_response_structure(self):
        """Verify validation error (422) response structure."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)

    def test_validation_error_contains_field_info(self):
        """Verify validation errors contain field information."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        data = r.json()
        # FastAPI validation errors include field information
        assert len(data["detail"]) > 0
        assert any("field" in str(err).lower() or "name" in str(err).lower() 
                   for err in data["detail"])

    def test_not_found_error_has_detail(self):
        """Verify 404 responses include detail field."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert data["detail"] == "not found"


class TestHTTPStatusCodes:
    """Tests for correct HTTP status codes across endpoints."""

    def test_health_returns_200(self):
        """Verify GET /health returns 200."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_create_item_success_returns_200(self):
        """Verify POST /items success returns 200."""
        r = client.post("/items", json={"name": "item", "price": 10})
        assert r.status_code == 200

    def test_create_item_validation_error_returns_422(self):
        """Verify POST /items validation error returns 422."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422

    def test_create_item_business_error_returns_400(self):
        """Verify POST /items business error (price) returns 400."""
        r = client.post("/items", json={"name": "item", "price": -1})
        assert r.status_code == 400

    def test_get_item_found_returns_200(self):
        """Verify GET /items/{id} for found item returns 200."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_not_found_returns_404(self):
        """Verify GET /items/{id} for missing item returns 404."""
        r = client.get("/items/999")
        assert r.status_code == 404

    def test_invalid_method_returns_error(self):
        """Verify invalid HTTP method returns error."""
        r = client.patch("/items/1")
        assert r.status_code in [405, 404]


class TestResponseContentTypes:
    """Tests for response content types and headers."""

    def test_json_response_content_type(self):
        """Verify responses include JSON content type."""
        r = client.post("/items", json={"name": "item", "price": 10})
        assert "application/json" in r.headers.get("content-type", "")

    def test_error_response_content_type(self):
        """Verify error responses include JSON content type."""
        r = client.post("/items", json={"name": "item", "price": -1})
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_response_content_type(self):
        """Verify GET response includes JSON content type."""
        r = client.get("/items/1")
        assert "application/json" in r.headers.get("content-type", "")


class TestErrorMessageConsistency:
    """Tests for error message clarity and consistency."""

    def test_price_error_message_clear(self):
        """Verify price validation error message is clear."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        detail = r.json()["detail"]
        assert "price" in detail.lower()
        assert "0" in detail or "positive" in detail.lower()

    def test_not_found_error_message_clear(self):
        """Verify 404 error message is clear."""
        r = client.get("/items/999")
        assert r.status_code == 404
        detail = r.json()["detail"]
        assert "not found" in detail.lower()

    @pytest.mark.parametrize("invalid_price", [-5, -100, 0, -0.01])
    def test_price_error_consistent_across_values(self, invalid_price):
        """Verify error message is consistent for all invalid prices."""
        r = client.post("/items", json={"name": "item", "price": invalid_price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]


class TestResponseDataIntegrity:
    """Tests for data integrity in responses."""

    def test_created_item_has_consistent_id(self):
        """Verify created items have id field."""
        r = client.post("/items", json={"name": "item1", "price": 10})
        assert r.json()["id"] == 1

    def test_get_item_id_matches_request(self):
        """Verify GET response returns correct item."""
        r = client.get("/items/1")
        assert r.json()["id"] == 1
        assert r.json()["name"] == "sample"
        assert r.json()["price"] == 10.0

    def test_multiple_creates_preserve_data(self):
        """Verify sequential creates don't corrupt data."""
        names = ["item1", "item2", "item3"]
        prices = [10.0, 20.0, 30.0]
        
        for name, price in zip(names, prices):
            r = client.post("/items", json={"name": name, "price": price})
            assert r.status_code == 200
            data = r.json()
            assert data["name"] == name
            assert data["price"] == price

    def test_special_characters_preserved_in_response(self):
        """Verify special characters are preserved in response."""
        r = client.post("/items", json={"name": "item-_!@#$%", "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == "item-_!@#$%"
