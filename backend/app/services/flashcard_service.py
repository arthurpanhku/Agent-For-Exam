"""Flashcard service — generate and schedule spaced-repetition cards.

Storage layout (JSON, per subject):
  uploads/metadata/flashcards/{subject_id}.json
  {
    "cards": {
      "<card_id>": {
        "card_id": str,
        "front": str,
        "back": str,
        "source_doc": str,
        "created_at": ISO str,
        "next_review": ISO str,    # SM-2 next review date
        "interval": int,           # days
        "repetitions": int,        # n
        "ease_factor": float,      # EF
        "last_quality": int | null
      }
    }
  }
"""
from __future__ import annotations

import json
import uuid
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

import app.config as config
from app.services.config_service import config_service

logger = config.get_logger("app.flashcard")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── SM-2 algorithm ────────────────────────────────────────────────────────────

def _sm2(repetitions: int, interval: int, ease_factor: float, quality: int):
    """One SM-2 step.  quality: 0 (blackout) … 5 (perfect).
    Returns (new_repetitions, new_interval, new_ease_factor).
    """
    if quality < 3:
        repetitions = 0
        interval = 1
    else:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval * ease_factor)
        repetitions += 1

    ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ease_factor = max(1.3, ease_factor)
    return repetitions, interval, ease_factor


# ── Storage helpers ──────────────────────────────────────────────────────────

class FlashcardService:
    def __init__(self) -> None:
        self._dir = Path(config.settings.conversations_metadata_dir) / "flashcards"
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, subject_id: str) -> Path:
        return self._dir / f"{subject_id}.json"

    def _load(self, subject_id: str) -> Dict:
        p = self._path(subject_id)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"cards": {}}

    def _save(self, subject_id: str, data: Dict) -> None:
        with open(self._path(subject_id), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ── LLM call ──────────────────────────────────────────────────────────────

    async def _call_llm(self, prompt: str) -> str:
        cfg = config_service.get_config("chat")
        api_key = cfg.get("api_key") or config.settings.chat_llm_binding_api_key
        base_url = (cfg.get("host") or config.settings.chat_llm_binding_host).rstrip("/")
        model = cfg.get("model") or config.settings.chat_llm_model

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
            "max_tokens": 4096,
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data["choices"][0]["message"]["content"]

    # ── Generation ────────────────────────────────────────────────────────────

    async def generate_cards(
        self, subject_id: str, subject_name: str, doc_texts: List[Dict[str, str]], n: int = 15
    ) -> List[Dict]:
        """Generate n flashcards from doc_texts using LLM and persist them."""
        combined = "\n\n".join(
            f"[Document: {d['filename']}]\n{d['text'][:3000]}" for d in doc_texts
        )
        prompt = f"""You are a study assistant. Based on the following course materials for "{subject_name}", generate exactly {n} high-quality flashcards.

Return ONLY a JSON array (no markdown, no extra text) in this format:
[
  {{"front": "Question or concept", "back": "Concise answer or definition", "source": "filename or 'general'"}},
  ...
]

Rules:
- Focus on key definitions, formulas, concepts, and relationships
- Front should be a clear question or incomplete statement
- Back should be concise (1-4 sentences max)
- Cover different topics across the materials
- Do NOT include trivial or purely administrative information

Materials:
{combined}"""

        raw = await self._call_llm(prompt)

        # Extract JSON array from response
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if not match:
            logger.warning("LLM returned no JSON array for flashcard generation")
            return []

        try:
            items = json.loads(match.group())
        except json.JSONDecodeError as e:
            logger.error("JSON parse error in flashcard generation: %s", e)
            return []

        data = self._load(subject_id)
        now = _now_iso()
        new_cards = []

        for item in items[:n]:
            card_id = str(uuid.uuid4())[:8]
            card = {
                "card_id": card_id,
                "front": item.get("front", ""),
                "back": item.get("back", ""),
                "source_doc": item.get("source", ""),
                "created_at": now,
                "next_review": now,
                "interval": 1,
                "repetitions": 0,
                "ease_factor": 2.5,
                "last_quality": None,
            }
            data["cards"][card_id] = card
            new_cards.append(card)

        self._save(subject_id, data)
        logger.info("Generated %d flashcards for subject %s", len(new_cards), subject_id)
        return new_cards

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def list_cards(self, subject_id: str) -> List[Dict]:
        return list(self._load(subject_id)["cards"].values())

    def get_due_cards(self, subject_id: str) -> List[Dict]:
        now = datetime.now(timezone.utc)
        cards = self.list_cards(subject_id)
        due = []
        for c in cards:
            try:
                next_rev = datetime.fromisoformat(c["next_review"])
                if next_rev.tzinfo is None:
                    next_rev = next_rev.replace(tzinfo=timezone.utc)
                if next_rev <= now:
                    due.append(c)
            except Exception:
                due.append(c)
        return due

    def review_card(self, subject_id: str, card_id: str, quality: int) -> Optional[Dict]:
        """Apply one SM-2 review step.  quality 0-5."""
        data = self._load(subject_id)
        card = data["cards"].get(card_id)
        if not card:
            return None

        reps, interval, ef = _sm2(
            card["repetitions"], card["interval"], card["ease_factor"], quality
        )
        card["repetitions"] = reps
        card["interval"] = interval
        card["ease_factor"] = round(ef, 4)
        card["last_quality"] = quality
        next_rev = datetime.now(timezone.utc) + timedelta(days=interval)
        card["next_review"] = next_rev.isoformat()

        data["cards"][card_id] = card
        self._save(subject_id, data)
        return card

    def delete_card(self, subject_id: str, card_id: str) -> bool:
        data = self._load(subject_id)
        if card_id in data["cards"]:
            del data["cards"][card_id]
            self._save(subject_id, data)
            return True
        return False

    def delete_all_cards(self, subject_id: str) -> int:
        data = self._load(subject_id)
        n = len(data["cards"])
        data["cards"] = {}
        self._save(subject_id, data)
        return n

    def stats(self, subject_id: str) -> Dict:
        cards = self.list_cards(subject_id)
        due = self.get_due_cards(subject_id)
        mastered = [c for c in cards if c["repetitions"] >= 3 and c.get("last_quality", 0) >= 4]
        return {
            "total": len(cards),
            "due": len(due),
            "mastered": len(mastered),
            "new": len([c for c in cards if c["repetitions"] == 0]),
        }
