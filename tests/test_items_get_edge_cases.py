import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get_item endpoint."""

    @pytest.mark.parametrize("item_id", [-1000, -100, -1])
    def test_get_item_with_negative_ids(self, item_id):
        """Negative IDs should return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [0, 2, 3, 10, 100, 1000])
    def test_get_item_with_various_valid_ids(self, item_id):
        """Various IDs should return either 200 or 404 depending on existence."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code in [200, 404]

    def test_get_item_with_very_large_id(self):
        """Very large ID should return 404."""
        r = client.get(f"/items/{999999999}")
        assert r.status_code == 404

    def test_get_item_with_id_one_returns_success(self):
        """ID 1 should return 200."""
        r = client.get("/items/1")
        assert r.status_code == 200


class TestCreateItemWithVaryingPrices:
    """Test create_item with various price values to ensure edge case handling."""

    @pytest.mark.parametrize("price", [0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0])
    def test_create_item_with_increasing_prices(self, price):
        """Various positive prices should all be accepted."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_create_item_with_float_precision(self):
        """Float precision should be maintained in responses."""
        price = 19.99
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_create_item_with_scientific_notation(self):
        """Scientific notation prices should be handled."""
        price = 1e3  # 1000
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price


class TestCreateItemWithVaryingNames:
    """Test create_item with various name values."""

    @pytest.mark.parametrize("name", ["", " ", "   "])
    def test_create_item_with_whitespace_only_names(self, name):
        """Whitespace names should be accepted (Pydantic doesn't validate content)."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize("name", ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")"])
    def test_create_item_with_single_special_characters(self, name):
        """Single special characters should be accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_with_json_like_name(self):
        """JSON-like string as name should be accepted."""
        name = '{"key": "value"}'
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_with_html_like_name(self):
        """HTML-like string as name should be accepted."""
        name = "<div>test</div>"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestCreateItemResponseConsistency:
    """Test consistency of create_item responses."""

    def test_create_item_response_id_is_always_one(self):
        """Response ID should always be 1 (per mock implementation)."""
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_create_item_response_preserves_input_name(self):
        """Response should preserve the exact input name."""
        test_names = ["product", "Book", "Item#1", "Test Item", "café"]
        for name in test_names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name

    def test_create_item_response_preserves_input_price(self):
        """Response should preserve the exact input price."""
        test_prices = [0.01, 1.5, 10.99, 99.99, 1000.0]
        for price in test_prices:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price


class TestGetItemResponseConsistency:
    """Test consistency of get_item responses."""

    def test_get_item_id_one_always_returns_same_data(self):
        """Multiple calls to get item 1 should return consistent data."""
        responses = []
        for _ in range(3):
            r = client.get("/items/1")
            assert r.status_code == 200
            responses.append(r.json())
        
        # All responses should be identical
        for resp in responses[1:]:
            assert resp == responses[0]

    def test_get_item_id_one_response_structure(self):
        """Item 1 should always return the expected structure."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_not_found_always_returns_404(self):
        """Multiple calls to non-existent items should return 404."""
        non_existent_ids = [2, 10, 100, 999]
        for item_id in non_existent_ids:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404
            assert r.json()["detail"] == "not found"


class TestCreateItemEdgeCasePrices:
    """Test edge case prices for create_item."""

    def test_create_item_with_minimum_positive_price(self):
        """Minimum positive price should be accepted."""
        r = client.post("/items", json={"name": "item", "price": 0.001})
        assert r.status_code == 200

    def test_create_item_with_price_just_above_zero(self):
        """Price just above zero should be accepted."""
        r = client.post("/items", json={"name": "item", "price": 0.0001})
        assert r.status_code == 200

    def test_create_item_with_price_at_boundary(self):
        """Price at various boundaries should be handled."""
        boundaries = [0.00000001, 1, 10, 100, 1000, 10000, 100000]
        for price in boundaries:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price


class TestRequestMethodValidation:
    """Test that endpoints properly validate HTTP methods."""

    def test_get_health_with_post_not_allowed(self):
        """POST to /health should not be allowed."""
        r = client.post("/health")
        assert r.status_code in [405, 422]  # Method not allowed or validation error

    def test_create_item_with_get_not_allowed(self):
        """GET to /items POST endpoint should not be allowed."""
        r = client.get("/items")
        assert r.status_code in [405, 404]  # Method not allowed or not found

    def test_get_item_with_post_not_allowed(self):
        """POST to /items/{id} GET endpoint should not be allowed."""
        r = client.post("/items/1")
        assert r.status_code in [405, 422]  # Method not allowed or validation error


class TestIntegrationScenarios:
    """Test integration scenarios across endpoints."""

    def test_create_and_verify_item_flow(self):
        """Test creating an item and verifying it works with get."""
        # Create an item
        create_r = client.post("/items", json={"name": "test_item", "price": 25.99})
        assert create_r.status_code == 200
        created_item = create_r.json()
        
        # The created item should have ID 1 (per mock implementation)
        assert created_item["id"] == 1
        
        # Get item 1 should return success
        get_r = client.get("/items/1")
        assert get_r.status_code == 200

    def test_multiple_create_operations(self):
        """Test multiple create operations."""
        for i in range(5):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
            assert r.json()["name"] == f"item{i}"

    def test_multiple_get_operations_mixed_ids(self):
        """Test getting existing and non-existing items."""
        results = []
        for item_id in [1, 2, 1, 999, 1, 0, -5]:
            r = client.get(f"/items/{item_id}")
            results.append((item_id, r.status_code))
        
        # ID 1 should always be found
        assert results[0][1] == 200
        assert results[2][1] == 200
        assert results[4][1] == 200
        
        # Non-existent IDs should return 404
        for item_id, status in results:
            if item_id != 1:
                assert status == 404


class TestErrorMessageContent:
    """Test the content and format of error messages."""

    def test_price_validation_error_message(self):
        """Price validation error should have specific message."""
        r = client.post("/items", json={"name": "test", "price": -1})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_not_found_error_message(self):
        """Not found error should have specific message."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_error_response_is_json_dict(self):
        """Error responses should be JSON dictionaries."""
        error_cases = [
            ("POST", "/items", {"name": "test", "price": 0}, 400),
            ("GET", "/items/999", None, 404),
        ]
        for method, path, json_body, expected_status in error_cases:
            if method == "POST":
                r = client.post(path, json=json_body)
            else:
                r = client.get(path)
            assert r.status_code == expected_status
            assert isinstance(r.json(), dict)
            assert "detail" in r.json()


class TestDataTypePreservation:
    """Test that data types are preserved through request-response cycle."""

    def test_price_float_type_preserved(self):
        """Price should be returned as number/float."""
        r = client.post("/items", json={"name": "test", "price": 10.5})
        assert r.status_code == 200
        price = r.json()["price"]
        assert isinstance(price, (int, float))
        assert price == 10.5

    def test_id_integer_type_preserved(self):
        """ID should be returned as integer."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        item_id = r.json()["id"]
        assert isinstance(item_id, int)

    def test_name_string_type_preserved(self):
        """Name should be returned as string."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        name = r.json()["name"]
        assert isinstance(name, str)
        assert name == "test"
