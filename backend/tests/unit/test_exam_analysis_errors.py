import asyncio

from app.services.exam_analysis.sub_agent import (
    ERROR_MODEL_REFUSAL,
    ERROR_NETWORK_TIMEOUT,
    ERROR_UNKNOWN,
    _classify_llm_error,
)


def test_classifies_timeout_exception():
    assert _classify_llm_error(asyncio.TimeoutError()) == ERROR_NETWORK_TIMEOUT


def test_classifies_provider_refusal_body():
    assert _classify_llm_error("provider error", status=400, body="content_filter policy") == ERROR_MODEL_REFUSAL


def test_classifies_unknown_error():
    assert _classify_llm_error("bad gateway", status=502) == ERROR_UNKNOWN
