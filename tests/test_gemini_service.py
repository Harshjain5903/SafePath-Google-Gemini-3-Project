"""
Tests for GeminiService retry behavior.
Uses a fake client so no network calls or API key are needed.
"""
import sys
from pathlib import Path

import pytest
from google.genai import errors

sys.path.insert(0, str(Path(__file__).parent.parent / "risk_aware_routing"))
import gemini_service  # noqa: E402
from gemini_service import GeminiService  # noqa: E402


class FakeModels:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def generate_content(self, **kwargs):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def make_service(outcomes):
    svc = GeminiService.__new__(GeminiService)
    svc.client = type("FakeClient", (), {})()
    svc.client.models = FakeModels(outcomes)
    return svc


def api_error(cls, code, status):
    return cls(code, {"error": {"code": code, "status": status, "message": status}})


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(gemini_service.time, "sleep", lambda s: None)


def test_retries_server_error_then_succeeds():
    svc = make_service([api_error(errors.ServerError, 503, "UNAVAILABLE"), "ok"])
    assert svc._generate(model="m", contents="hi") == "ok"
    assert svc.client.models.calls == 2


def test_gives_up_after_max_retries():
    err = api_error(errors.ServerError, 503, "UNAVAILABLE")
    svc = make_service([err, err, err])
    with pytest.raises(errors.ServerError):
        svc._generate(model="m", contents="hi")
    assert svc.client.models.calls == 3


def test_quota_error_not_retried():
    svc = make_service([api_error(errors.ClientError, 429, "RESOURCE_EXHAUSTED"), "ok"])
    with pytest.raises(errors.ClientError):
        svc._generate(model="m", contents="hi")
    assert svc.client.models.calls == 1
