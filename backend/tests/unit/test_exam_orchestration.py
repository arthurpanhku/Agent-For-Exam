"""Unit tests for exam_analysis orchestration helpers."""
import pytest
from app.services.exam_analysis.orchestration import _flatten_questions


class _Q:
    """Minimal question stub."""
    def __init__(self, qid, content="", index=0, sub_questions=None):
        self.id = qid
        self.content = content
        self.index = index
        self.sub_questions = sub_questions or []


class TestFlattenQuestions:
    def test_flat_list(self):
        questions = [_Q("q1"), _Q("q2"), _Q("q3")]
        result = _flatten_questions(questions)
        assert len(result) == 3
        assert [r["id"] for r in result] == ["q1", "q2", "q3"]

    def test_nested_sub_questions(self):
        sub1 = _Q("q1a")
        sub2 = _Q("q1b")
        parent = _Q("q1", sub_questions=[sub1, sub2])
        result = _flatten_questions([parent])
        assert len(result) == 2
        assert result[0]["id"] == "q1a"
        assert result[1]["id"] == "q1b"

    def test_mixed_flat_and_nested(self):
        q1 = _Q("q1", sub_questions=[_Q("q1a"), _Q("q1b")])
        q2 = _Q("q2")
        result = _flatten_questions([q1, q2])
        assert len(result) == 3
        ids = [r["id"] for r in result]
        assert "q1a" in ids
        assert "q1b" in ids
        assert "q2" in ids

    def test_empty_input(self):
        assert _flatten_questions([]) == []

    def test_deeply_nested(self):
        leaf = _Q("leaf")
        mid = _Q("mid", sub_questions=[leaf])
        root = _Q("root", sub_questions=[mid])
        result = _flatten_questions([root])
        assert len(result) == 1
        assert result[0]["id"] == "leaf"

    def test_content_and_index_preserved(self):
        q = _Q("q1", content="What is X?", index=5)
        result = _flatten_questions([q])
        assert result[0]["content"] == "What is X?"
        assert result[0]["index"] == 5
