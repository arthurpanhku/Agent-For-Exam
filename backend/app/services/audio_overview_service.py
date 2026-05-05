"""Audio Overview service — generate a podcast-style dialogue script.

Storage: uploads/metadata/audio_overviews/{subject_id}.json
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp

import app.config as config
from app.services.config_service import config_service

logger = config.get_logger("app.audio_overview")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AudioOverviewService:
    def __init__(self) -> None:
        self._dir = Path(config.settings.conversations_metadata_dir) / "audio_overviews"
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, subject_id: str) -> Path:
        return self._dir / f"{subject_id}.json"

    def _load(self, subject_id: str) -> Optional[Dict]:
        p = self._path(subject_id)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def _save(self, subject_id: str, data: Dict) -> None:
        with open(self._path(subject_id), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_overview(self, subject_id: str) -> Optional[Dict]:
        return self._load(subject_id)

    def delete_overview(self, subject_id: str) -> bool:
        p = self._path(subject_id)
        if p.exists():
            p.unlink()
            return True
        return False

    async def _call_llm(self, prompt: str) -> str:
        cfg = config_service.get_config("chat")
        api_key = cfg.get("api_key") or config.settings.chat_llm_binding_api_key
        base_url = (cfg.get("host") or config.settings.chat_llm_binding_host).rstrip("/")
        model = cfg.get("model") or config.settings.chat_llm_model

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
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

    async def generate_overview(
        self,
        subject_id: str,
        subject_name: str,
        doc_texts: List[Dict[str, str]],
    ) -> Dict:
        """Generate a podcast-style dialogue and persist it."""
        combined = "\n\n".join(
            f"[Document: {d['filename']}]\n{d['text'][:2500]}" for d in doc_texts
        )

        prompt = f"""You are producing a short educational podcast episode about "{subject_name}".

Write a natural, engaging two-host dialogue (Host A = "Alex", Host B = "Sam") that covers the KEY concepts from the materials below.

Requirements:
- 8-12 dialogue turns total (alternating speakers)
- Opening hook that grabs attention
- Cover 3-5 core concepts with clear explanations
- Use analogies and examples
- Closing summary with a memorable takeaway
- Conversational tone — not a lecture

Return ONLY a JSON array (no markdown fences) like:
[
  {{"speaker": "Alex", "text": "..."}},
  {{"speaker": "Sam",  "text": "..."}},
  ...
]

Materials:
{combined}"""

        raw = await self._call_llm(prompt)

        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if not match:
            raise ValueError("LLM did not return a JSON array")

        script = json.loads(match.group())

        overview = {
            "subject_id": subject_id,
            "subject_name": subject_name,
            "generated_at": _now_iso(),
            "script": script,
            "doc_count": len(doc_texts),
        }
        self._save(subject_id, overview)
        logger.info("Audio overview generated for subject %s (%d turns)", subject_id, len(script))
        return overview
