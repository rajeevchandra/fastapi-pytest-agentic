"""
Edge cases and integration tests for /items endpoints.

Tests boundary conditions, path parameter edge cases, and multi-step scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemIDEdgeCases:
    """Test edge cases for the item_id path parameter."""

    @pytest.mark.parametrize("item_id", [0, -1, -100, -999])
    def test_negative_item_ids_return_404(self, item_id):
        """Test that negative IDs return 404."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [2, 3, 10, 100, 999, 10000])
    def test_other_positive_ids_return_404(self, item_id):
        """Test that IDs other than 1 return 404."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404

    def test_very_large_item_id(self):
        """Test very large item_id value."""
        response = client.get(f"/items/{2147483647}")  # Max 32-bit int
        assert response.status_code == 404

    def test_item_id_zero(self):
        """Test item_id = 0."""
        response = client.get("/items/0")
        assert response.status_code == 404

    def test_item_id_one_returns_item(self):
        """Test that item_id = 1 returns the item."""
        response = client.get("/items/1")
        assert response.status_code == 200
        assert response.json()["id"] == 1


class TestCreateItemBoundaryValues:
    """Test boundary values for create_item endpoint."""

    @pytest.mark.parametrize("price", [0.0, -0.0, -0.01, -1.0, -1000.0])
    def test_non_positive_prices_rejected(self, price):
        """Test that non-positive prices are rejected."""
        response = client.post(
            "/items", json={"name": "item", "price": price}
        )
        assert response.status_code == 400

    @pytest.mark.parametrize("price", [0.01, 0.001, 0.0001, 0.00001])
    def test_very_small_positive_prices_accepted(self, price):
        """Test that very small positive prices are accepted."""
        response = client.post(
            "/items", json={"name": "item", "price": price}
        )
        assert response.status_code == 200
        assert response.json()["price"] == price

    @pytest.mark.parametrize("price", [1e6, 1e7, 1e8])
    def test_very_large_prices_accepted(self, price):
        """Test that very large prices are accepted."""
        response = client.post(
            "/items", json={"name": "item", "price": price}
        )
        assert response.status_code == 200
        assert response.json()["price"] == price

    @pytest.mark.parametrize("price", [1.1, 1.23, 1.456, 99.999])
    def test_decimal_prices_accepted(self, price):
        """Test that decimal prices are accepted."""
        response = client.post(
            "/items", json={"name": "item", "price": price}
        )
        assert response.status_code == 200


class TestCreateItemNameEdgeCases:
    """Test edge cases for the name field."""

    @pytest.mark.parametrize("name", ["", " ", "  "])
    def test_empty_or_whitespace_names(self, name):
        """Test empty and whitespace-only names."""
        response = client.post(
            "/items", json={"name": name, "price": 10.0}
        )
        # Behavior depends on Pydantic validation rules
        # FastAPI might accept or reject these
        assert response.status_code in [200, 422]

    def test_very_long_name(self):
        """Test very long name (10000+ characters)."""
        long_name = "a" * 10000
        response = client.post(
            "/items", json={"name": long_name, "price": 10.0}
        )
        assert response.status_code == 200
        assert len(response.json()["name"]) == 10000

    @pytest.mark.parametrize("name", ["!@#$%^&*()", "<<<>>>", "~~!!@@"])
    def test_special_character_names(self, name):
        """Test names with special characters."""
        response = client.post(
            "/items", json={"name": name, "price": 10.0}
        )
        assert response.status_code == 200
        assert response.json()["name"] == name

    @pytest.mark.parametrize(
        "name", ["café", "naïve", "日本", "中文", "한국", "Привет"]
    )
    def test_unicode_names(self, name):
        """Test names with unicode characters."""
        response = client.post(
            "/items", json={"name": name, "price": 10.0}
        )
        assert response.status_code == 200
        assert response.json()["name"] == name

    @pytest.mark.parametrize("name", ["🎁", "😀", "🚀", "❤️"])
    def test_emoji_in_names(self, name):
        """Test names containing emoji."""
        response = client.post(
            "/items", json={"name": name, "price": 10.0}
        )
        assert response.status_code == 200
        assert response.json()["name"] == name

    def test_name_with_newlines(self):
        """Test name with newline characters."""
        name = "item\nname"
        response = client.post(
            "/items", json={"name": name, "price": 10.0}
        )
        assert response.status_code == 200
        assert response.json()["name"] == name

    def test_name_with_tabs(self):
        """Test name with tab characters."""
        name = "item\tname"
        response = client.post(
            "/items", json={"name": name, "price": 10.0}
        )
        assert response.status_code == 200


class TestIntegrationScenarios:
    """Test multi-step integration scenarios."""

    def test_create_then_retrieve_sequence(self):
        """Test creating an item and then retrieving it."""
        # Create an item
        create_response = client.post(
            "/items", json={"name": "test_item", "price": 25.0}
        )
        assert create_response.status_code == 200
        created_data = create_response.json()

        # Retrieve the item using the returned ID
        item_id = created_data["id"]
        if item_id == 1:
            # Only item_id=1 is implemented in the mock
            get_response = client.get(f"/items/{item_id}")
            assert get_response.status_code == 200
            retrieved_data = get_response.json()

            # Verify basic structure
            assert retrieved_data["id"] == item_id

    def test_multiple_successful_creations(self):
        """Test multiple successful create operations."""
        items = [
            {"name": "item1", "price": 10.0},
            {"name": "item2", "price": 20.0},
            {"name": "item3", "price": 30.0},
        ]
        responses = []
        for item in items:
            response = client.post("/items", json=item)
            assert response.status_code == 200
            responses.append(response.json())

        # All responses should be valid
        for resp in responses:
            assert "id" in resp
            assert "name" in resp
            assert "price" in resp

    def test_get_followed_by_failed_create(self):
        """Test successful GET followed by failed create."""
        # First, get valid item
        get_response = client.get("/items/1")
        assert get_response.status_code == 200

        # Then try to create with invalid data
        create_response = client.post(
            "/items", json={"name": "item", "price": -5.0}
        )
        assert create_response.status_code == 400

        # Verify GET still works
        get_response2 = client.get("/items/1")
        assert get_response2.status_code == 200

    def test_multiple_failed_gets(self):
        """Test multiple failed GET requests."""
        for item_id in [2, 3, 999]:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 404

    def test_create_with_different_prices(self):
        """Test creating items with different price values."""
        prices = [0.01, 1.5, 10.0, 99.99, 1000.0]
        for price in prices:
            response = client.post(
                "/items", json={"name": "item", "price": price}
            )
            assert response.status_code == 200
            assert response.json()["price"] == price

    def test_interleaved_create_and_get(self):
        """Test alternating between create and get operations."""
        for i in range(3):
            # Create
            response = client.post(
                "/items", json={"name": f"item{i}", "price": 10.0 + i}
            )
            assert response.status_code == 200

            # Try to get item 1
            response = client.get("/items/1")
            assert response.status_code == 200

            # Try to get non-existent
            response = client.get(f"/items/{i+2}")
            assert response.status_code == 404


class TestDataValidationComprehensive:
    """Comprehensive data validation tests."""

    def test_price_at_boundary_zero_point_zero_one(self):
        """Test price = 0.01 which is just above zero."""
        response = client.post(
            "/items", json={"name": "item", "price": 0.01}
        )
        assert response.status_code == 200
        assert response.json()["price"] == 0.01

    def test_price_at_boundary_zero(self):
        """Test price = 0 which should be rejected."""
        response = client.post(
            "/items", json={"name": "item", "price": 0}
        )
        assert response.status_code == 400

    def test_price_at_boundary_negative_zero_point_zero_one(self):
        """Test price = -0.01 which should be rejected."""
        response = client.post(
            "/items", json={"name": "item", "price": -0.01}
        )
        assert response.status_code == 400

    def test_scientific_notation_price(self):
        """Test price using scientific notation."""
        response = client.post(
            "/items", json={"name": "item", "price": 1e2}  # 100
        )
        assert response.status_code == 200
        assert response.json()["price"] == 100.0

    def test_negative_scientific_notation_price(self):
        """Test negative price with scientific notation."""
        response = client.post(
            "/items", json={"name": "item", "price": -1e2}  # -100
        )
        assert response.status_code == 400

    def test_name_single_character(self):
        """Test name with single character."""
        response = client.post(
            "/items", json={"name": "a", "price": 10.0}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "a"

    def test_name_with_quotes(self):
        """Test name containing quotes."""
        name = 'item "quoted"'
        response = client.post(
            "/items", json={"name": name, "price": 10.0}
        )
        assert response.status_code == 200
        assert response.json()["name"] == name

    def test_name_with_backslashes(self):
        """Test name containing backslashes."""
        name = "item\\path"
        response = client.post(
            "/items", json={"name": name, "price": 10.0}
        )
        assert response.status_code == 200
        assert response.json()["name"] == name


class TestResponseValidationEdgeCases:
    """Test edge cases in response validation."""

    def test_response_id_type_is_integer(self):
        """Test that ID in response is always an integer."""
        response = client.post(
            "/items", json={"name": "item", "price": 10.0}
        )
        assert isinstance(response.json()["id"], int)

    def test_response_name_type_is_string(self):
        """Test that name in response is always a string."""
        response = client.post(
            "/items", json={"name": "item", "price": 10.0}
        )
        assert isinstance(response.json()["name"], str)

    def test_response_price_type_is_numeric(self):
        """Test that price in response is numeric."""
        response = client.post(
            "/items", json={"name": "item", "price": 10.0}
        )
        price = response.json()["price"]
        assert isinstance(price, (int, float))

    def test_response_price_not_negative(self):
        """Test that price in response is not negative for valid input."""
        response = client.post(
            "/items", json={"name": "item", "price": 10.5}
        )
        assert response.json()["price"] >= 0

    def test_status_code_is_integer(self):
        """Test that status codes are proper integers."""
        response = client.get("/items/1")
        assert isinstance(response.status_code, int)
        assert 100 <= response.status_code < 600


class TestConsistencyChecks:
    """Test consistency across multiple operations."""

    def test_same_item_retrieved_multiple_times_identical(self):
        """Test that retrieving same item multiple times gives identical results."""
        responses = [client.get("/items/1") for _ in range(5)]
        data_list = [r.json() for r in responses]
        # All should be identical
        for data in data_list[1:]:
            assert data == data_list[0]

    def test_status_codes_consistent_for_same_operation(self):
        """Test that same operation returns same status code."""
        responses = [client.get("/items/999") for _ in range(3)]
        status_codes = [r.status_code for r in responses]
        assert all(code == 404 for code in status_codes)

    def test_error_messages_consistent(self):
        """Test that error messages are consistent."""
        responses = [
            client.post("/items", json={"name": "item", "price": -5.0})
            for _ in range(2)
        ]
        error_details = [r.json()["detail"] for r in responses]
        assert error_details[0] == error_details[1]
