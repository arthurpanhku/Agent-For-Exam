"""Analytics service — study activity stats for the dashboard."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List

import app.config as config
from app.services.flashcard_service import FlashcardService

logger = config.get_logger("app.analytics")

_flashcard_svc = FlashcardService()


class AnalyticsService:
    def __init__(self) -> None:
        self._meta_dir = Path(config.settings.conversations_metadata_dir)
        self._data_dir = Path(config.settings.data_dir)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _load_json(self, path: Path) -> Dict:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _all_subjects(self) -> Dict:
        data = self._load_json(self._meta_dir / "subjects.json")
        return data.get("subjects", {})

    def _all_conversations(self) -> Dict:
        data = self._load_json(self._meta_dir / "conversations.json")
        return data.get("conversations", {})

    def _all_docs_for_subject(self, subject_id: str) -> List[Dict]:
        data = self._load_json(self._meta_dir / "subject_documents.json")
        docs = data.get("documents", {})
        return [d for d in docs.values() if d.get("subject_id") == subject_id]

    def _all_docs(self) -> Dict:
        data = self._load_json(self._meta_dir / "subject_documents.json")
        return data.get("documents", {})

    # ── Global dashboard ─────────────────────────────────────────────────────

    def global_stats(self) -> Dict:
        subjects = self._all_subjects()
        conversations = self._all_conversations()
        docs = self._all_docs()

        # Count exams
        exam_meta_path = self._data_dir / "exams" / "metadata.json"
        exam_data = self._load_json(exam_meta_path)
        exams = exam_data.get("exams", {})

        # Activity calendar — last 365 days, daily counts
        activity: Dict[str, int] = defaultdict(int)
        for conv in conversations.values():
            ts = conv.get("updated_at") or conv.get("created_at", "")
            if ts:
                try:
                    day = ts[:10]
                    activity[day] += 1
                except Exception:
                    pass
        for doc in docs.values():
            ts = doc.get("uploaded_at") or doc.get("created_at", "")
            if ts:
                try:
                    activity[ts[:10]] += 1
                except Exception:
                    pass

        # Compute 30-day active streak
        streak = 0
        today = datetime.now(timezone.utc).date()
        for i in range(365):
            day = (today - timedelta(days=i)).isoformat()
            if activity.get(day, 0) > 0:
                if i == 0 or streak > 0:
                    streak += 1
            elif i > 0:
                break

        return {
            "subjects": len(subjects),
            "conversations": len(conversations),
            "documents": len(docs),
            "exams": len(exams),
            "streak_days": streak,
            "activity_calendar": dict(activity),
        }

    # ── Per-subject stats ─────────────────────────────────────────────────────

    def subject_stats(self, subject_id: str) -> Dict:
        conversations = self._all_conversations()
        subj_convs = [c for c in conversations.values() if c.get("subject_id") == subject_id]
        docs = self._all_docs_for_subject(subject_id)
        fc_stats = _flashcard_svc.stats(subject_id)

        # Knowledge coverage by topic — approximate from doc filenames / titles
        topic_map = _build_topic_map(docs)

        # Activity last 30 days
        activity: Dict[str, int] = defaultdict(int)
        for conv in subj_convs:
            ts = conv.get("updated_at") or conv.get("created_at", "")
            if ts:
                try:
                    activity[ts[:10]] += 1
                except Exception:
                    pass

        return {
            "subject_id": subject_id,
            "conversations": len(subj_convs),
            "documents": len(docs),
            "flashcards": fc_stats,
            "topic_coverage": topic_map,
            "activity_30d": dict(activity),
        }


def _build_topic_map(docs: List[Dict]) -> List[Dict]:
    """Return radar-chart-friendly topic list from document metadata."""
    # Use document filenames as topic proxies; limit to 8
    topics = []
    seen = set()
    for doc in docs[:8]:
        name = doc.get("original_filename") or doc.get("filename") or "Unknown"
        stem = Path(name).stem[:20]
        if stem not in seen:
            seen.add(stem)
            topics.append({"name": stem, "value": 1})
    return topics
