"""Comprehensive edge cases and integration scenario testing."""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestCreateItemPriceBoundaryConditions:
    """Comprehensive price boundary and edge case testing."""

    @pytest.mark.parametrize(
        "price",
        [
            0.001,
            0.01,
            0.1,
            1,
            10,
            100,
            1000,
            10000,
            99999.99,
            100000.00,
            1000000,
            1e6,
            1e7,
            1e10,
        ],
    )
    def test_create_item_accepts_wide_price_range(self, price):
        """Test that wide range of valid prices are accepted."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize(
        "price",
        [
            -1000,
            -100,
            -10,
            -1,
            -0.1,
            -0.01,
            -0.001,
            0,
        ],
    )
    def test_create_item_rejects_zero_and_negative_prices(self, price):
        """Test comprehensive negative price rejection."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400

    def test_create_item_price_precision_small_decimal(self):
        """Test handling of precise decimal values."""
        r = client.post("/items", json={"name": "test", "price": 0.001})
        assert r.status_code == 200
        # Check that precision is maintained
        assert r.json()["price"] == 0.001

    def test_create_item_price_precision_large_decimal(self):
        """Test large number with decimal precision."""
        r = client.post("/items", json={"name": "test", "price": 9999.99})
        assert r.status_code == 200
        assert r.json()["price"] == 9999.99


class TestCreateItemNameEdgeCases:
    """Comprehensive name field edge cases."""

    @pytest.mark.parametrize(
        "name",
        [
            "a",
            "a" * 100,
            "a" * 1000,
            "a" * 5000,
        ],
    )
    def test_create_item_with_various_length_names(self, name):
        """Test names of various lengths."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize(
        "name",
        [
            "test@domain.com",
            "user#123",
            "item$price",
            "name%value",
            "test^item",
            "check&verify",
            "path/to/item",
            "item\\with\\backslash",
            "line\nbreak",
            "tab\ttab",
        ],
    )
    def test_create_item_with_special_characters(self, name):
        """Test names with various special characters."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize(
        "name",
        [
            "café",
            "Москва",
            "北京",
            "🎉 emoji",
            "test™",
            "naïve",
        ],
    )
    def test_create_item_with_unicode_characters(self, name):
        """Test names with various unicode characters."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize(
        "name",
        [
            " ",
            "  ",
            "   ",
            "\n",
            "\t",
            "\r\n",
        ],
    )
    def test_create_item_with_whitespace_names(self, name):
        """Test names consisting of whitespace."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_name_with_leading_trailing_spaces(self):
        """Test name with leading and trailing spaces."""
        name = "  centered  "
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestGetItemBoundaryConditions:
    """Comprehensive boundary testing for get_item."""

    @pytest.mark.parametrize(
        "item_id",
        [
            2,
            3,
            10,
            100,
            1000,
            10000,
            100000,
            999999,
            9999999,
        ],
    )
    def test_get_item_returns_404_for_all_non_one_ids(self, item_id):
        """Test that only item ID 1 succeeds."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize(
        "item_id",
        [
            -1,
            -2,
            -10,
            -100,
            -1000,
            -999999,
        ],
    )
    def test_get_item_returns_404_for_negative_ids(self, item_id):
        """Test that negative IDs all return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404


class TestErrorHandlingComprehensive:
    """Comprehensive error handling scenarios."""

    def test_create_item_zero_price_error_message(self):
        """Test specific error message for zero price."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        assert "must be > 0" in r.json()["detail"]

    def test_create_item_negative_price_error_message(self):
        """Test specific error message for negative price."""
        r = client.post("/items", json={"name": "test", "price": -50})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_get_item_not_found_error_exact_message(self):
        """Test exact error message for not found."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("missing_field", ["name", "price"])
    def test_create_item_missing_field_returns_422(self, missing_field):
        """Test that any missing field returns 422."""
        payload = {"name": "test", "price": 10.0}
        del payload[missing_field]
        r = client.post("/items", json=payload)
        assert r.status_code == 422

    def test_create_item_invalid_json_content_type(self):
        """Test request with non-JSON content."""
        r = client.post("/items", data="invalid", headers={"Content-Type": "text/plain"})
        # FastAPI should reject this
        assert r.status_code in [422, 400, 415]

    def test_get_item_invalid_path_parameter_type(self):
        """Test get_item with non-integer path parameter."""
        r = client.get("/items/not_an_integer")
        # FastAPI type validation should catch this
        assert r.status_code == 422


class TestResponseDataConsistency:
    """Test consistency of response data across requests."""

    def test_create_item_response_always_has_id_one(self):
        """Test that created items always have ID 1."""
        for i in range(1, 6):
            r = client.post("/items", json={"name": f"item{i}", "price": float(i)})
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_get_item_one_returns_consistent_data(self):
        """Test that GET /items/1 always returns same data."""
        for _ in range(3):
            r = client.get("/items/1")
            assert r.status_code == 200
            data = r.json()
            assert data == {"id": 1, "name": "sample", "price": 10.0}

    def test_get_item_returns_backend_data_not_post_data(self):
        """Test that GET endpoint returns backend data, not posted data."""
        # Post a different item
        post_r = client.post("/items", json={"name": "posted_name", "price": 50.0})
        assert post_r.status_code == 200

        # Get should return backend's "sample" not our "posted_name"
        get_r = client.get("/items/1")
        assert get_r.status_code == 200
        assert get_r.json()["name"] == "sample"
        assert get_r.json()["price"] == 10.0


class TestAllEndpointsStatusCodes:
    """Test status codes for all possible scenarios."""

    def test_all_success_endpoints_return_200(self):
        """Test that successful requests return 200."""
        # Health
        assert client.get("/health").status_code == 200
        # Create
        assert (
            client.post("/items", json={"name": "test", "price": 10.0}).status_code
            == 200
        )
        # Get valid
        assert client.get("/items/1").status_code == 200

    def test_get_invalid_id_returns_404(self):
        """Test that invalid IDs return 404."""
        for item_id in [0, 2, 999, -1]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404

    def test_create_invalid_price_returns_400(self):
        """Test that invalid prices return 400."""
        for price in [0, -1, -100]:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 400

    def test_missing_fields_return_422(self):
        """Test that missing fields return 422."""
        assert client.post("/items", json={"price": 10.0}).status_code == 422
        assert client.post("/items", json={"name": "test"}).status_code == 422
        assert client.post("/items", json={}).status_code == 422


class TestMethodValidation:
    """Test that endpoints only accept correct HTTP methods."""

    def test_health_get_success(self):
        """Test that GET /health works."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_get_item_with_get_success(self):
        """Test that GET /items/{id} works."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_create_item_with_post_success(self):
        """Test that POST /items works."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200


class TestComplexIntegrationScenarios:
    """Complex integration and edge case scenarios."""

    def test_create_item_with_unicode_then_get(self):
        """Test create with unicode name and then retrieve."""
        create_r = client.post("/items", json={"name": "日本語テスト", "price": 100.0})
        assert create_r.status_code == 200
        assert create_r.json()["name"] == "日本語テスト"

        # Backend doesn't persist, so retrieve gets "sample"
        get_r = client.get("/items/1")
        assert get_r.status_code == 200
        assert get_r.json()["name"] == "sample"

    def test_create_with_large_price_boundary(self):
        """Test creating item with very large price."""
        large_price = 999999999.99
        r = client.post("/items", json={"name": "expensive", "price": large_price})
        assert r.status_code == 200
        assert r.json()["price"] == large_price

    def test_create_with_tiny_price_boundary(self):
        """Test creating item with very small positive price."""
        tiny_price = 0.0001
        r = client.post("/items", json={"name": "cheap", "price": tiny_price})
        assert r.status_code == 200
        assert r.json()["price"] == tiny_price

    def test_request_response_roundtrip_consistency(self):
        """Test that request and response data are consistent."""
        test_data = {"name": "roundtrip_test", "price": 42.50}
        r = client.post("/items", json=test_data)

        assert r.status_code == 200
        response_data = r.json()

        # Check that what we sent is what we got back
        assert response_data["name"] == test_data["name"]
        assert response_data["price"] == test_data["price"]

    def test_multiple_sequential_invalid_then_valid(self):
        """Test multiple invalid requests followed by valid."""
        # Invalid
        r1 = client.post("/items", json={"name": "test", "price": 0})
        assert r1.status_code == 400

        r2 = client.post("/items", json={"name": "test", "price": -10})
        assert r2.status_code == 400

        # Valid should still work
        r3 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r3.status_code == 200

    def test_get_all_status_codes_in_sequence(self):
        """Test getting various status codes in sequence."""
        # 200 success
        assert client.get("/items/1").status_code == 200

        # 404 not found
        assert client.get("/items/999").status_code == 404

        # 200 success again
        assert client.get("/items/1").status_code == 200

        # 404 again
        assert client.get("/items/0").status_code == 404


class TestDataTypeHandlingEdgeCases:
    """Test edge cases in data type handling."""

    def test_price_integer_converted_to_float(self):
        """Test that integer prices are handled correctly."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        # Should be stored as number
        assert r.json()["price"] == 10

    def test_price_scientific_notation(self):
        """Test price in scientific notation."""
        r = client.post("/items", json={"name": "test", "price": 1e3})
        assert r.status_code == 200
        assert r.json()["price"] == 1e3

    def test_response_always_dict(self):
        """Test that response is always a dictionary."""
        r = client.get("/items/1")
        assert isinstance(r.json(), dict)

        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert isinstance(r.json(), dict)

        r = client.get("/health")
        assert isinstance(r.json(), dict)

    def test_error_response_always_dict(self):
        """Test that error responses are always dictionaries."""
        r = client.get("/items/999")
        assert isinstance(r.json(), dict)

        r = client.post("/items", json={"name": "test", "price": 0})
        assert isinstance(r.json(), dict)


class TestNameFieldUnicodeNormalization:
    """Test unicode name handling in detail."""

    def test_name_with_combining_characters(self):
        """Test name with combining unicode characters."""
        # 'é' can be represented as 'e' + combining acute
        name = "café"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        # Verify it's stored as we sent it
        assert r.json()["name"] == name

    def test_name_with_emoji_variations(self):
        """Test various emoji in name."""
        names = ["test 🎉", "emoji 😀", "item ❤️"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name


class TestPriceCalculationEdgeCases:
    """Test price-related edge cases."""

    def test_price_exactly_one_cent(self):
        """Test price of exactly one cent."""
        r = client.post("/items", json={"name": "test", "price": 0.01})
        assert r.status_code == 200
        assert r.json()["price"] == 0.01

    def test_price_just_above_zero(self):
        """Test price just above zero."""
        r = client.post("/items", json={"name": "test", "price": 0.00001})
        assert r.status_code == 200
        assert r.json()["price"] == 0.00001

    def test_price_rounding_not_needed(self):
        """Test that prices don't need rounding."""
        price = 19.99
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price
