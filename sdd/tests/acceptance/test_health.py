"""Smoke test: the health check needs no token (NFR-002)."""


def test_health_needs_no_token(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
