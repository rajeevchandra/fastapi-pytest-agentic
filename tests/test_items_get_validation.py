import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemBoundaryValues:
    """Tests for GET /items/{item_id} with boundary values."""

    def test_get_item_with_item_id_zero(self):
        """Test that item_id=0 returns 404 (not found)."""
        r = client.get("/items/0")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_with_negative_item_id(self):
        """Test that negative item_id returns 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_get_item_with_negative_large_item_id(self):
        """Test that large negative item_id returns 404."""
        r = client.get("/items/-999999")
        assert r.status_code == 404

    def test_get_item_with_very_large_item_id(self):
        """Test that very large item_id returns 404."""
        r = client.get("/items/999999999999")
        assert r.status_code == 404

    def test_get_item_with_max_int_value(self):
        """Test with maximum integer value."""
        r = client.get(f"/items/{2**31 - 1}")
        assert r.status_code == 404

    def test_get_item_with_item_id_two(self):
        """Test that item_id=2 returns 404 (not found)."""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_with_item_id_three(self):
        """Test that item_id=3 returns 404."""
        r = client.get("/items/3")
        assert r.status_code == 404

    def test_get_item_with_item_id_hundred(self):
        """Test that item_id=100 returns 404."""
        r = client.get("/items/100")
        assert r.status_code == 404

    def test_get_item_with_only_valid_id(self):
        """Test that only item_id=1 returns 200."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_id_one_has_correct_response_structure(self):
        """Test that item_id=1 response has required fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_id_one_returns_correct_data(self):
        """Test that item_id=1 returns known values."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_not_found_has_detail_field(self):
        """Test that 404 response includes detail field."""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert "detail" in r.json()

    def test_get_item_not_found_detail_message(self):
        """Test that 404 detail message is correct."""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"


class TestGetItemPathParameterValidation:
    """Tests for path parameter validation."""

    def test_get_item_with_string_item_id(self):
        """Test that string item_id that cannot be parsed returns 422."""
        r = client.get("/items/abc")
        assert r.status_code == 422

    def test_get_item_with_float_item_id(self):
        """Test that float item_id is handled (depends on FastAPI config)."""
        r = client.get("/items/1.5")
        # FastAPI might parse this as string or convert it; we test for non-500
        assert r.status_code in [404, 422]

    def test_get_item_with_special_characters(self):
        """Test that special characters in path return 422."""
        r = client.get("/items/!@#$")
        assert r.status_code == 422

    def test_get_item_with_unicode_characters(self):
        """Test that unicode characters in path return 422."""
        r = client.get("/items/中文")
        assert r.status_code == 422


class TestGetItemContentType:
    """Tests for response headers and content types."""

    def test_get_item_response_content_type_json(self):
        """Test that successful response is JSON."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_item_not_found_content_type_json(self):
        """Test that 404 response is also JSON."""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_item_response_is_valid_json(self):
        """Test that response can be parsed as JSON."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)

    def test_get_item_not_found_response_is_valid_json(self):
        """Test that 404 response is valid JSON."""
        r = client.get("/items/2")
        assert r.status_code == 404
        data = r.json()
        assert isinstance(data, dict)


class TestGetItemResponseData:
    """Tests for response data correctness."""

    def test_get_item_id_type_is_int(self):
        """Test that returned id is an integer."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert isinstance(r.json()["id"], int)

    def test_get_item_name_type_is_string(self):
        """Test that returned name is a string."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert isinstance(r.json()["name"], str)

    def test_get_item_price_type_is_number(self):
        """Test that returned price is a number."""
        r = client.get("/items/1")
        assert r.status_code == 200
        price = r.json()["price"]
        assert isinstance(price, (int, float))

    def test_get_item_price_value_is_positive(self):
        """Test that returned price is positive."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["price"] > 0


class TestGetItemMultipleCalls:
    """Tests for calling the endpoint multiple times."""

    def test_get_item_same_id_multiple_times_consistent(self):
        """Test that multiple calls return consistent data."""
        results = []
        for _ in range(5):
            r = client.get("/items/1")
            assert r.status_code == 200
            results.append(r.json())
        
        # All results should be identical
        first = results[0]
        for result in results[1:]:
            assert result == first

    def test_get_item_alternating_valid_invalid_ids(self):
        """Test alternating between valid and invalid item IDs."""
        r1 = client.get("/items/1")
        assert r1.status_code == 200
        
        r2 = client.get("/items/2")
        assert r2.status_code == 404
        
        r3 = client.get("/items/1")
        assert r3.status_code == 200
        
        r4 = client.get("/items/99")
        assert r4.status_code == 404

    @pytest.mark.parametrize("item_id", [2, 3, 5, 10, 50, 100])
    def test_get_item_various_non_existent_ids_return_404(self, item_id):
        """Test that various non-existent IDs return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [-1, 0, -100])
    def test_get_item_various_invalid_ids_return_404(self, item_id):
        """Test that various invalid IDs return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404


class TestGetItemErrorMessages:
    """Tests for error message consistency and content."""

    def test_get_item_404_has_message(self):
        """Test that 404 responses include a message."""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert "detail" in r.json()
        assert len(r.json()["detail"]) > 0

    def test_get_item_422_has_error_info(self):
        """Test that 422 responses have error information."""
        r = client.get("/items/invalid")
        assert r.status_code == 422
        assert "detail" in r.json() or len(r.json()) > 0

    def test_get_item_success_no_error_detail(self):
        """Test that successful response doesn't have 'detail' field."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "detail" not in r.json()


class TestGetItemUrlEncoding:
    """Tests for URL encoding edge cases."""

    def test_get_item_with_url_encoded_string(self):
        """Test that URL-encoded strings are handled."""
        r = client.get("/items/%20")  # space character
        assert r.status_code == 422

    def test_get_item_with_empty_path_segment(self):
        """Test behavior with empty path (missing item_id)."""
        r = client.get("/items/")
        # This might be handled differently - could redirect or 404
        assert r.status_code in [307, 404, 422]
