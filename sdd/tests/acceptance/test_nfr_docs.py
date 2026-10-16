"""NFR-007: the running app describes every operation in contracts/api.md, with its error responses."""

import pytest

# Endpoint → error statuses the contract lists for it (401 comes from the shared auth dependency).
CONTRACT = {
    ("get", "/health"): set(),
    ("post", "/auth/register"): {"409", "422"},
    ("post", "/auth/login"): {"401", "422"},
    ("get", "/users/me"): {"401"},
    ("get", "/rooms"): set(),
    ("get", "/rooms/{room_id}"): {"404", "422"},
    ("post", "/rooms"): {"403", "409", "422"},
    ("patch", "/rooms/{room_id}"): {"403", "404", "409", "422"},
    ("get", "/rooms/{room_id}/availability"): {"404", "422"},
    ("post", "/bookings"): {"404", "409", "422"},
    ("get", "/bookings/me"): set(),
    ("delete", "/bookings/{booking_id}"): {"403", "404", "409", "422"},
}


@pytest.fixture(scope="module")
def spec():
    from fastapi.testclient import TestClient

    from app.main import create_app

    with TestClient(create_app(":memory:")) as c:
        r = c.get("/openapi.json")
        assert r.status_code == 200
        return r.json()


@pytest.mark.parametrize("method, path", sorted(CONTRACT))
def test_contract_endpoint_documented_with_its_errors(spec, method, path):
    operation = spec["paths"].get(path, {}).get(method)
    assert operation is not None, f"{method.upper()} {path} missing from /openapi.json"
    documented = set(operation.get("responses", {}))
    assert CONTRACT[(method, path)] <= documented, f"undocumented errors: {CONTRACT[(method, path)] - documented}"


def test_no_undocumented_endpoints(spec):
    actual = {(m, p) for p, ops in spec["paths"].items() for m in ops}
    assert actual == set(CONTRACT), f"not in the contract: {actual - set(CONTRACT)}"


def test_interactive_docs_available(client):
    assert client.get("/docs").status_code == 200
