from __future__ import annotations

from app.ai.models import AIClassificationResult


def test_default_values():
    r = AIClassificationResult()
    assert r.is_advertisement is False
    assert r.confidence == 0.0
    assert r.score == 0
    assert r.reasons == []
    assert r.summary is None
    assert r.model is None
    assert r.provider is None
    assert r.error is None


def test_to_dict():
    r = AIClassificationResult(
        is_advertisement=True,
        confidence=0.95,
        score=95,
        reasons=["contains link", "scam pattern"],
        summary="Suspicious",
        model="gpt-4o-mini",
        provider="openai",
    )
    d = r.to_dict()
    assert d["is_advertisement"] is True
    assert d["confidence"] == 0.95
    assert d["score"] == 95
    assert d["reasons"] == ["contains link", "scam pattern"]
    assert d["summary"] == "Suspicious"
    assert d["model"] == "gpt-4o-mini"
    assert d["provider"] == "openai"
    assert "error" not in d


def test_to_dict_with_error():
    r = AIClassificationResult(error="something went wrong", is_advertisement=False)
    d = r.to_dict()
    assert "error" not in d
    assert d["is_advertisement"] is False


def test_error_survives():
    r = AIClassificationResult(error="API error")
    assert r.error == "API error"
