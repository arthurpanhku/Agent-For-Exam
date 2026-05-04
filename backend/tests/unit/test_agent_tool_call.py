"""Unit tests for agent_service tool_call normalization helpers."""
import json
import pytest
from app.services.agent.agent_service import _normalize_tool_call, _normalize_tool_calls


class TestNormalizeToolCall:
    def test_valid_tool_call(self):
        tc = {
            "id": "call_abc",
            "type": "function",
            "function": {"name": "query_knowledge_graph", "arguments": '{"query": "test"}'},
        }
        result = _normalize_tool_call(tc)
        assert result is not None
        assert result["id"] == "call_abc"
        assert result["function"]["name"] == "query_knowledge_graph"
        assert result["function"]["arguments"] == '{"query": "test"}'

    def test_dict_arguments_converted_to_json_string(self):
        tc = {
            "id": "call_1",
            "type": "function",
            "function": {"name": "list_documents", "arguments": {"key": "val"}},
        }
        result = _normalize_tool_call(tc)
        assert result is not None
        assert isinstance(result["function"]["arguments"], str)
        assert json.loads(result["function"]["arguments"]) == {"key": "val"}

    def test_missing_id_gets_generated(self):
        tc = {
            "type": "function",
            "function": {"name": "generate_mindmap", "arguments": "{}"},
        }
        result = _normalize_tool_call(tc)
        assert result is not None
        assert result["id"].startswith("call_")

    def test_empty_name_returns_none(self):
        tc = {"id": "x", "type": "function", "function": {"name": "", "arguments": "{}"}}
        assert _normalize_tool_call(tc) is None

    def test_non_dict_returns_none(self):
        assert _normalize_tool_call("not a dict") is None
        assert _normalize_tool_call(None) is None

    def test_missing_function_key_returns_none(self):
        assert _normalize_tool_call({"id": "x", "type": "function"}) is None

    def test_none_arguments_become_empty_object(self):
        tc = {"id": "x", "type": "function", "function": {"name": "read", "arguments": None}}
        result = _normalize_tool_call(tc)
        assert result is not None
        assert result["function"]["arguments"] == "{}"


class TestNormalizeToolCalls:
    def test_filters_invalid_entries(self):
        calls = [
            {"id": "a", "type": "function", "function": {"name": "read", "arguments": "{}"}},
            None,
            {"id": "b", "type": "function", "function": {"name": "", "arguments": "{}"}},
        ]
        result = _normalize_tool_calls(calls)
        assert len(result) == 1
        assert result[0]["function"]["name"] == "read"

    def test_empty_list(self):
        assert _normalize_tool_calls([]) == []

    def test_all_valid(self):
        calls = [
            {"id": f"call_{i}", "type": "function", "function": {"name": f"tool_{i}", "arguments": "{}"}}
            for i in range(3)
        ]
        result = _normalize_tool_calls(calls)
        assert len(result) == 3
