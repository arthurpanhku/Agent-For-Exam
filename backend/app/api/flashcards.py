"""Flashcard API routes."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.services.flashcard_service import FlashcardService
from app.services.document_service import DocumentService
from app.utils.document_parser import DocumentParser
from pathlib import Path
import app.config as config

router = APIRouter(prefix="/api/subjects/{subject_id}/flashcards", tags=["flashcards"])

_svc = FlashcardService()
_doc_svc = DocumentService()
_parser = DocumentParser()


# ── Schemas ───────────────────────────────────────────────────────────────────

class CardOut(BaseModel):
    card_id: str
    front: str
    back: str
    source_doc: str
    created_at: str
    next_review: str
    interval: int
    repetitions: int
    ease_factor: float
    last_quality: Optional[int] = None


class ReviewRequest(BaseModel):
    quality: int = Field(..., ge=0, le=5, description="SM-2 quality 0 (blackout) – 5 (perfect)")


class GenerateRequest(BaseModel):
    n: int = Field(default=15, ge=5, le=30, description="Number of cards to generate")


class StatsOut(BaseModel):
    total: int
    due: int
    mastered: int
    new: int


# ── Helper ────────────────────────────────────────────────────────────────────

def _get_doc_texts(subject_id: str) -> list:
    """Collect parsed text for all completed documents in the subject."""
    docs = _doc_svc.list_documents_for_subject(subject_id)
    results = []
    for doc in docs:
        if doc.get("status") != "completed":
            continue
        fp = doc.get("file_path")
        if not fp:
            continue
        try:
            resolved = Path(fp)
            if not resolved.is_absolute():
                resolved = Path(config.settings.conversations_metadata_dir).parent / fp
            if resolved.exists():
                text = _parser.extract_text(str(resolved), file_id=doc.get("file_id", ""))
                results.append({
                    "filename": doc.get("original_filename") or doc.get("filename", ""),
                    "text": text[:5000],
                })
        except Exception:
            pass
    return results


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("", response_model=List[CardOut])
def list_cards(subject_id: str):
    return _svc.list_cards(subject_id)


@router.get("/due", response_model=List[CardOut])
def due_cards(subject_id: str):
    return _svc.get_due_cards(subject_id)


@router.get("/stats", response_model=StatsOut)
def stats(subject_id: str):
    return _svc.stats(subject_id)


@router.post("/generate", response_model=List[CardOut], status_code=201)
async def generate(subject_id: str, body: GenerateRequest):
    from app.services.subject_service import SubjectService
    subj_svc = SubjectService()
    subj = subj_svc.get_subject(subject_id)
    if not subj:
        raise HTTPException(404, "Subject not found")

    doc_texts = _get_doc_texts(subject_id)
    if not doc_texts:
        raise HTTPException(422, "No completed documents found for this subject — upload and index documents first.")

    cards = await _svc.generate_cards(
        subject_id=subject_id,
        subject_name=subj.get("name", subject_id),
        doc_texts=doc_texts,
        n=body.n,
    )
    return cards


@router.post("/{card_id}/review", response_model=CardOut)
def review(subject_id: str, card_id: str, body: ReviewRequest):
    card = _svc.review_card(subject_id, card_id, body.quality)
    if not card:
        raise HTTPException(404, "Card not found")
    return card


@router.delete("/{card_id}", status_code=204)
def delete_card(subject_id: str, card_id: str):
    if not _svc.delete_card(subject_id, card_id):
        raise HTTPException(404, "Card not found")


@router.delete("", status_code=200)
def delete_all(subject_id: str):
    n = _svc.delete_all_cards(subject_id)
    return {"deleted": n}
