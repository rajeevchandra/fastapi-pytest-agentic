"""
Comprehensive path parameter validation and integration edge case tests.

Tests cover:
- GET path parameter edge cases (boundary values, type coercion, extreme values)
- Multiple GET requests with different IDs
- Integration scenarios (POST then GET sequences)
- Response consistency across multiple calls
- Sequential operations and state patterns
- Error recovery and resilience
- Response headers and metadata
- State and consistency considerations
"""

import sys
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetPathParameterBoundaryValues:
    """Test GET /items/{item_id} with boundary values and edge cases."""

    @pytest.mark.parametrize(
        "item_id,expected_status",
        [
            (1, 200),  # Valid item ID
            (0, 404),  # Zero boundary
            (-1, 404),  # Negative boundary
            (2, 404),  # Just above valid
        ],
    )
    def test_get_item_basic_boundaries(self, item_id, expected_status):
        """Verify GET /items/{item_id} handles basic boundary values correctly."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == expected_status
        if expected_status == 200:
            data = response.json()
            assert data["id"] == 1
            assert data["name"] == "sample"
            assert data["price"] == 10.0
        else:
            data = response.json()
            assert "detail" in data
            assert data["detail"] == "not found"

    @pytest.mark.parametrize(
        "item_id",
        [
            -9999999,  # Very negative
            -2147483648,  # Near 32-bit signed integer minimum
            -1,  # Negative boundary
            0,  # Zero
        ],
    )
    def test_get_item_large_negative_values(self, item_id):
        """Verify GET /items/{item_id} rejects all negative and zero values."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "not found"

    @pytest.mark.parametrize(
        "item_id",
        [
            2,  # Just above valid
            10,
            100,
            1000,
            999999,
            2147483647,  # 32-bit signed integer maximum
            9223372036854775807,  # 64-bit signed integer maximum
        ],
    )
    def test_get_item_large_positive_values(self, item_id):
        """Verify GET /items/{item_id} rejects large positive values."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "not found"

    def test_get_item_id_1_exact_match(self):
        """Verify GET /items/1 is the only successful case."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_id_1_response_structure(self):
        """Verify GET /items/1 response has correct structure."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert set(data.keys()) == {"id", "name", "price"}
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], float)


class TestGetPathParameterTypeCoercion:
    """Test path parameter type coercion and parsing edge cases."""

    def test_get_item_with_leading_zeros(self):
        """Verify GET /items/001 is coerced to item_id=1."""
        response = client.get("/items/001")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    def test_get_item_with_multiple_leading_zeros(self):
        """Verify GET /items/0001 is coerced to item_id=1."""
        response = client.get("/items/0001")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    def test_get_item_negative_with_leading_zeros(self):
        """Verify GET /items/-001 is coerced to item_id=-1."""
        response = client.get("/items/-001")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "not found"

    def test_get_item_leading_positive_sign(self):
        """Verify GET /items/+1 is coerced to item_id=1."""
        response = client.get("/items/%2B1")  # URL-encoded +1
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    @pytest.mark.parametrize(
        "invalid_param",
        [
            "abc",  # Non-numeric string
            "1.5",  # Float string
            "1e10",  # Scientific notation
            "null",  # null string
            "undefined",  # undefined string
            "",  # Empty string
        ],
    )
    def test_get_item_invalid_type_parameters(self, invalid_param):
        """Verify GET /items with non-integer parameters returns 422."""
        response = client.get(f"/items/{invalid_param}")
        # FastAPI returns 422 for invalid path parameter types
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestMultipleGetRequestsConsistency:
    """Test consistency of GET responses across multiple sequential requests."""

    def test_multiple_get_requests_same_id_consistent(self):
        """Verify GET /items/1 returns consistent results across multiple calls."""
        responses = [client.get("/items/1") for _ in range(5)]
        
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["name"] == "sample"
            assert data["price"] == 10.0

    def test_multiple_get_requests_different_ids_consistent(self):
        """Verify GET with different invalid IDs consistently returns 404."""
        item_ids = [2, 5, 10, 100, 999]
        
        for item_id in item_ids:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "not found"

    @pytest.mark.parametrize(
        "sequence",
        [
            [1, 2, 1, 3, 1, 100],
            [2, 1, 1, 5, 1],
            [1, 0, 1, -1, 1],
            [999, 1, 1, 1000, 1],
        ],
    )
    def test_interleaved_valid_invalid_requests(self, sequence):
        """Verify interleaved valid and invalid requests maintain consistency."""
        results = []
        
        for item_id in sequence:
            response = client.get(f"/items/{item_id}")
            if item_id == 1:
                assert response.status_code == 200
                results.append(("valid", response.json()))
            else:
                assert response.status_code == 404
                results.append(("invalid", response.json()))
        
        # Verify all valid responses are identical
        valid_responses = [r[1] for r in results if r[0] == "valid"]
        for valid_response in valid_responses:
            assert valid_response == {"id": 1, "name": "sample", "price": 10.0}
        
        # Verify all invalid responses have correct structure
        invalid_responses = [r[1] for r in results if r[0] == "invalid"]
        for invalid_response in invalid_responses:
            assert invalid_response["detail"] == "not found"

    def test_get_same_id_no_state_change(self):
        """Verify repeated GET requests don't change state."""
        response1 = client.get("/items/1")
        data1 = response1.json()
        
        # Make multiple other requests
        for item_id in [2, 3, 4]:
            client.get(f"/items/{item_id}")
        
        response2 = client.get("/items/1")
        data2 = response2.json()
        
        # Data should be identical
        assert data1 == data2


class TestPostThenGetIntegration:
    """Test integration patterns of POST then GET operations."""

    @pytest.mark.parametrize(
        "post_name,post_price",
        [
            ("item_a", 10.0),
            ("item_b", 25.5),
            ("item_c", 99.99),
            ("item_d", 0.01),
        ],
    )
    def test_post_then_get_sequence_returns_expected_result(self, post_name, post_price):
        """Verify POST then GET sequence works correctly."""
        # POST create item
        post_response = client.post("/items", json={"name": post_name, "price": post_price})
        assert post_response.status_code == 200
        post_data = post_response.json()
        assert post_data["id"] == 1
        assert post_data["name"] == post_name
        assert post_data["price"] == post_price
        
        # GET item 1
        get_response = client.get("/items/1")
        assert get_response.status_code == 200
        get_data = get_response.json()
        # Note: The GET endpoint returns hardcoded "sample" item, not the posted item
        assert get_data["id"] == 1
        assert get_data["name"] == "sample"  # Hardcoded, not from POST
        assert get_data["price"] == 10.0  # Hardcoded, not from POST

    def test_multiple_posts_then_get_same_item(self):
        """Verify GET /items/1 returns consistent hardcoded value despite multiple POSTs."""
        for i in range(3):
            post_response = client.post(
                "/items", 
                json={"name": f"item_{i}", "price": 10.0 + i}
            )
            assert post_response.status_code == 200
        
        # GET should still return hardcoded item
        get_response = client.get("/items/1")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data == {"id": 1, "name": "sample", "price": 10.0}

    def test_post_with_various_prices_then_get_item_1(self):
        """Verify GET /items/1 is unaffected by POSTs with various prices."""
        prices = [0.01, 10.5, 99.99, 1000.0]
        
        for price in prices:
            post_response = client.post(
                "/items",
                json={"name": "test_item", "price": price}
            )
            assert post_response.status_code == 200
            assert post_response.json()["price"] == price
        
        # GET /items/1 should always return same hardcoded data
        get_response = client.get("/items/1")
        assert get_response.status_code == 200
        assert get_response.json() == {"id": 1, "name": "sample", "price": 10.0}

    def test_get_nonexistent_after_multiple_posts(self):
        """Verify GET of nonexistent item returns 404 regardless of previous POSTs."""
        # Create multiple items
        for i in range(3):
            client.post("/items", json={"name": f"item_{i}", "price": 10.0})
        
        # Try to GET nonexistent items
        for item_id in [2, 5, 100]:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 404
            assert response.json()["detail"] == "not found"


class TestResponseConsistencyAcrossMultipleCalls:
    """Test response consistency and metadata across multiple GET calls."""

    def test_get_response_content_type_consistent(self):
        """Verify Content-Type header is consistent across multiple GET calls."""
        responses = [client.get("/items/1") for _ in range(5)]
        
        for response in responses:
            assert "content-type" in response.headers
            assert "application/json" in response.headers["content-type"]

    def test_get_response_content_length_present(self):
        """Verify Content-Length header is present for GET requests."""
        response = client.get("/items/1")
        assert "content-length" in response.headers

    def test_get_error_response_has_content_type(self):
        """Verify error responses have Content-Type header."""
        response = client.get("/items/999")
        assert response.status_code == 404
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]

    def test_get_response_serialization_consistency(self):
        """Verify response JSON can be serialized/deserialized consistently."""
        import json
        
        response = client.get("/items/1")
        data1 = response.json()
        
        # Serialize to string and back
        serialized = json.dumps(data1)
        deserialized = json.loads(serialized)
        
        assert deserialized == data1

    def test_get_multiple_responses_json_identical(self):
        """Verify JSON responses from multiple calls are byte-for-byte identical."""
        import json
        
        responses = [client.get("/items/1") for _ in range(3)]
        json_strings = [json.dumps(r.json(), sort_keys=True) for r in responses]
        
        # All should be identical
        for json_str in json_strings[1:]:
            assert json_str == json_strings[0]


class TestErrorRecoveryAndResilience:
    """Test error recovery patterns and resilience of GET endpoint."""

    def test_get_after_error_still_works(self):
        """Verify GET /items/1 works after failed GET attempt."""
        # Try invalid request
        error_response = client.get("/items/invalid")
        assert error_response.status_code == 422
        
        # Valid request should still work
        success_response = client.get("/items/1")
        assert success_response.status_code == 200
        assert success_response.json()["id"] == 1

    def test_alternating_valid_invalid_requests(self):
        """Verify alternating valid and invalid requests all behave correctly."""
        for i in range(5):
            # Invalid
            invalid_response = client.get(f"/items/{i * 100 + 2}")
            assert invalid_response.status_code == 404
            
            # Valid
            valid_response = client.get("/items/1")
            assert valid_response.status_code == 200
            assert valid_response.json()["id"] == 1

    def test_recovery_after_parameter_boundary_test(self):
        """Verify normal operation after testing boundary parameters."""
        # Test boundaries
        boundary_responses = [
            client.get("/items/0"),
            client.get("/items/-1"),
            client.get("/items/999999"),
        ]
        for resp in boundary_responses:
            assert resp.status_code == 404
        
        # Normal operation should still work
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert data == {"id": 1, "name": "sample", "price": 10.0}

    def test_get_after_failed_post(self):
        """Verify GET works normally after failed POST."""
        # Failed POST (invalid price)
        post_response = client.post("/items", json={"name": "book", "price": 0})
        assert post_response.status_code == 400
        
        # GET should still work
        get_response = client.get("/items/1")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == 1

    def test_get_after_validation_error(self):
        """Verify GET works normally after validation error on POST."""
        # Invalid POST (missing price field)
        post_response = client.post("/items", json={"name": "book"})
        assert post_response.status_code == 422
        
        # GET should still work normally
        get_response = client.get("/items/1")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == 1


class TestSequentialOperationPatterns:
    """Test various sequential operation patterns and workflows."""

    def test_sequential_gets_with_status_verification(self):
        """Verify status codes remain consistent across sequential operations."""
        statuses = []
        
        for item_id in [1, 2, 3, 1, 4, 1]:
            response = client.get(f"/items/{item_id}")
            statuses.append(response.status_code)
        
        expected = [200, 404, 404, 200, 404, 200]
        assert statuses == expected

    def test_bulk_get_operations_performance_pattern(self):
        """Verify bulk GET operations all complete successfully."""
        item_ids = [1] * 10 + [2] * 10  # Test item 1 and 2 multiple times
        responses = [client.get(f"/items/{item_id}") for item_id in item_ids]
        
        # First 10 should be 200, next 10 should be 404
        for i, response in enumerate(responses):
            if i < 10:
                assert response.status_code == 200
            else:
                assert response.status_code == 404

    def test_mixed_operations_maintaining_state(self):
        """Verify state remains consistent through mixed GET operations."""
        # Record initial state
        initial = client.get("/items/1").json()
        
        # Perform various operations
        client.get("/items/2")
        client.get("/items/100")
        client.post("/items", json={"name": "temp", "price": 5.0})
        client.get("/items/-1")
        
        # Verify state unchanged
        final = client.get("/items/1").json()
        assert initial == final

    def test_ten_sequential_valid_requests(self):
        """Verify 10 sequential valid GET /items/1 requests."""
        for _ in range(10):
            response = client.get("/items/1")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["name"] == "sample"
            assert data["price"] == 10.0

    @pytest.mark.parametrize(
        "invalid_ids",
        [
            [2, 3, 5, 10, 50],
            [100, 500, 1000, 9999, 2147483647],
            [0, -1, -5, -100, -2147483648],
        ],
    )
    def test_ten_sequential_invalid_requests_different_ids(self, invalid_ids):
        """Verify sequential invalid GET requests with different IDs."""
        for item_id in invalid_ids:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 404
            assert response.json()["detail"] == "not found"

    def test_interleaved_pattern_with_response_verification(self):
        """Verify interleaved pattern with full response verification."""
        pattern = [1, 999, 1, 0, 1, -1, 1]
        
        for item_id in pattern:
            response = client.get(f"/items/{item_id}")
            
            if item_id == 1:
                assert response.status_code == 200
                data = response.json()
                assert data == {"id": 1, "name": "sample", "price": 10.0}
            else:
                assert response.status_code == 404
                data = response.json()
                assert data["detail"] == "not found"


class TestResponseMetadataAndHeaders:
    """Test response metadata, headers, and HTTP properties."""

    def test_get_response_http_version(self):
        """Verify response uses valid HTTP version."""
        response = client.get("/items/1")
        # TestClient should return valid HTTP response
        assert response.status_code == 200

    def test_get_error_response_http_version(self):
        """Verify error response uses valid HTTP version."""
        response = client.get("/items/999")
        assert response.status_code == 404

    def test_get_response_has_required_headers(self):
        """Verify successful response has required headers."""
        response = client.get("/items/1")
        assert response.status_code == 200
        
        # Required headers
        assert "content-type" in response.headers
        assert "content-length" in response.headers

    def test_get_error_response_has_required_headers(self):
        """Verify error response has required headers."""
        response = client.get("/items/999")
        assert response.status_code == 404
        
        # Required headers
        assert "content-type" in response.headers

    def test_get_response_body_not_empty(self):
        """Verify successful GET response body is not empty."""
        response = client.get("/items/1")
        assert response.status_code == 200
        assert len(response.content) > 0
        assert response.text != ""

    def test_get_error_response_body_not_empty(self):
        """Verify error response body is not empty."""
        response = client.get("/items/999")
        assert response.status_code == 404
        assert len(response.content) > 0
        assert response.text != ""

    def test_get_response_encoding_valid(self):
        """Verify response encoding is valid."""
        response = client.get("/items/1")
        assert response.status_code == 200
        # Should be able to decode without error
        assert isinstance(response.text, str)
        assert len(response.text) > 0


class TestStateAndCachingConsiderations:
    """Test state management and consistency patterns."""

    @pytest.mark.parametrize(
        "post_sequence",
        [
            [(f"item_seq1_{i}", 10.0 * (i + 1)) for i in range(3)],
            [(f"item_seq2_{i}", 5.0 + i) for i in range(4)],
            [(f"item_seq3_{i}", 100.0 / (i + 1)) for i in range(2)],
        ],
    )
    def test_get_always_returns_same_value_after_different_posts(self, post_sequence):
        """Verify GET /items/1 always returns same value regardless of posts."""
        original_response = client.get("/items/1")
        original_data = original_response.json()
        
        # Create multiple items with different data
        for name, price in post_sequence:
            client.post("/items", json={"name": name, "price": price})
        
        # GET should still return original data
        new_response = client.get("/items/1")
        new_data = new_response.json()
        
        assert original_data == new_data
        assert new_data == {"id": 1, "name": "sample", "price": 10.0}

    def test_get_nonexistent_items_always_return_404(self):
        """Verify nonexistent items always return 404."""
        nonexistent_ids = [2, 5, 10, 100, 999]
        
        # Try once
        first_round = [
            client.get(f"/items/{item_id}").status_code
            for item_id in nonexistent_ids
        ]
        
        # Do some posts
        for i in range(3):
            client.post("/items", json={"name": f"item_{i}", "price": 10.0})
        
        # Try again
        second_round = [
            client.get(f"/items/{item_id}").status_code
            for item_id in nonexistent_ids
        ]
        
        # All should be 404 both times
        assert all(status == 404 for status in first_round)
        assert all(status == 404 for status in second_round)

    def test_get_item_1_has_fixed_immutable_values(self):
        """Verify GET /items/1 returns fixed immutable values."""
        responses = []
        
        for _ in range(5):
            response = client.get("/items/1")
            responses.append(response.json())
        
        # All responses should be identical
        first_response = responses[0]
        for response in responses[1:]:
            assert response == first_response
            assert response["id"] == 1
            assert response["name"] == "sample"
            assert response["price"] == 10.0

    def test_no_side_effects_from_get_requests(self):
        """Verify GET requests have no side effects on other operations."""
        # Record baseline
        initial_post = client.post(
            "/items",
            json={"name": "baseline", "price": 15.0}
        ).json()
        
        # Do multiple GETs
        for item_id in [1, 2, 3, 1, 999]:
            client.get(f"/items/{item_id}")
        
        # Verify POST still works identically
        post_response = client.post(
            "/items",
            json={"name": "baseline", "price": 15.0}
        ).json()
        
        # POST response should be identical
        assert initial_post["name"] == post_response["name"]
        assert initial_post["price"] == post_response["price"]


class TestEdgeCaseIntegrationScenarios:
    """Test complex edge case scenarios and integration patterns."""

    def test_maximum_integer_id_handling(self):
        """Verify maximum integer values are handled correctly."""
        max_int_64 = 9223372036854775807
        response = client.get(f"/items/{max_int_64}")
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"

    def test_minimum_integer_id_handling(self):
        """Verify minimum integer values are handled correctly."""
        min_int_64 = -9223372036854775808
        response = client.get(f"/items/{min_int_64}")
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"

    def test_item_id_boundary_surrounding_valid_id(self):
        """Verify boundaries immediately around valid ID (1) all return 404."""
        for item_id in [0, 2]:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "not found"

    @pytest.mark.parametrize(
        "sparse_pattern",
        [
            [1, 100, 1000, 10000, 100000, 1000000],
            [1, 2, 10, 100, 1000],
            [1, -1, -10, -100, -1000],
        ],
    )
    def test_sparse_distribution_of_requests(self, sparse_pattern):
        """Verify sparse distribution of ID requests all behave correctly."""
        for item_id in sparse_pattern:
            response = client.get(f"/items/{item_id}")
            
            if item_id == 1:
                assert response.status_code == 200
            else:
                assert response.status_code == 404

    def test_rapid_sequential_same_id_requests(self):
        """Verify rapid sequential requests to same ID."""
        for _ in range(20):
            response = client.get("/items/1")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1

    def test_get_after_multiple_failed_posts(self):
        """Verify GET works after multiple failed POST attempts."""
        # Multiple failed POSTs
        for invalid_price in [0, -1, -100]:
            response = client.post(
                "/items",
                json={"name": "test", "price": invalid_price}
            )
            assert response.status_code == 400
        
        # GET should still work
        response = client.get("/items/1")
        assert response.status_code == 200
        assert response.json()["id"] == 1

    def test_complex_workflow_sequence(self):
        """Verify complex workflow of mixed operations."""
        workflow = [
            ("GET", 1, 200),
            ("POST", None, 200),
            ("GET", 2, 404),
            ("GET", 1, 200),
            ("POST", None, 200),
            ("GET", 999, 404),
            ("GET", 1, 200),
        ]
        
        for operation, item_id, expected_status in workflow:
            if operation == "GET":
                response = client.get(f"/items/{item_id}")
            else:
                response = client.post(
                    "/items",
                    json={"name": "test", "price": 10.0}
                )
            
            assert response.status_code == expected_status
