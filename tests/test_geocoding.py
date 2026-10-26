"""
Tests for Mapbox Search Box geocoding (suggest -> retrieve, forward fallback).
HTTP calls are faked; no token or network needed.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "risk_aware_routing"))
import geocoding  # noqa: E402


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def feature(lng, lat):
    return {"features": [{"geometry": {"coordinates": [lng, lat]}}]}


@pytest.fixture
def fake_http(monkeypatch):
    """Route fake responses by endpoint; record which endpoints were hit."""
    routes = {}
    calls = []

    def fake_get(url, params=None, timeout=None):
        endpoint = url.rsplit("/v1/", 1)[1].split("/")[0]
        calls.append((endpoint, params))
        return FakeResponse(routes[endpoint])

    monkeypatch.setattr(geocoding.http_requests, "get", fake_get)
    monkeypatch.setattr(geocoding, "_geocode_cache", {})
    return routes, calls


def test_uses_suggest_then_retrieve(fake_http):
    routes, calls = fake_http
    routes["suggest"] = {"suggestions": [{"mapbox_id": "abc"}]}
    routes["retrieve"] = feature(-87.6051, 41.8919)

    assert geocoding.geocode_place("Navy Pier") == [41.8919, -87.6051]
    assert [c[0] for c in calls] == ["suggest", "retrieve"]
    assert calls[0][1]["q"] == "Navy Pier"


def test_falls_back_to_forward_when_no_suggestions(fake_http):
    routes, calls = fake_http
    routes["suggest"] = {"suggestions": []}
    routes["forward"] = feature(-87.6324, 41.8820)

    assert geocoding.geocode_place("the Loop") == [41.8820, -87.6324]
    assert [c[0] for c in calls] == ["suggest", "forward"]
    assert calls[1][1]["q"] == "the Loop, Chicago, Illinois"


def test_raises_when_nothing_found(fake_http):
    routes, _ = fake_http
    routes["suggest"] = {"suggestions": []}
    routes["forward"] = {"features": []}

    with pytest.raises(ValueError):
        geocoding.geocode_place("Nowhereville")


def test_caches_by_normalized_name(fake_http):
    routes, calls = fake_http
    routes["suggest"] = {"suggestions": [{"mapbox_id": "abc"}]}
    routes["retrieve"] = feature(-87.6226, 41.8826)

    geocoding.geocode_place("Millennium Park")
    geocoding.geocode_place("  millennium park ")
    assert len(calls) == 2  # second lookup served from cache


def test_proximity_uses_user_coords(fake_http):
    routes, calls = fake_http
    routes["suggest"] = {"suggestions": [{"mapbox_id": "abc"}]}
    routes["retrieve"] = feature(-87.65, 41.95)

    geocoding.geocode_place("Wrigley Field", user_coords=[41.9, -87.7])
    assert calls[0][1]["proximity"] == "-87.7,41.9"
