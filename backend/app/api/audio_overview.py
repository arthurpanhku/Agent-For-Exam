"""Audio Overview API routes."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException

import app.config as config
from app.services.audio_overview_service import AudioOverviewService
from app.services.subject_service import SubjectService
from app.services.document_service import DocumentService
from app.utils.document_parser import DocumentParser

router = APIRouter(prefix="/api/subjects/{subject_id}/audio-overview", tags=["audio-overview"])

_svc = AudioOverviewService()
_subj_svc = SubjectService()
_doc_svc = DocumentService()
_parser = DocumentParser()


def _get_doc_texts(subject_id: str) -> list:
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
                    "text": text[:3000],
                })
        except Exception:
            pass
    return results


@router.get("")
def get_overview(subject_id: str):
    data = _svc.get_overview(subject_id)
    if not data:
        raise HTTPException(404, "No audio overview generated yet")
    return data


@router.post("", status_code=201)
async def generate_overview(subject_id: str):
    subj = _subj_svc.get_subject(subject_id)
    if not subj:
        raise HTTPException(404, "Subject not found")

    doc_texts = _get_doc_texts(subject_id)
    if not doc_texts:
        raise HTTPException(422, "No completed documents — upload and index documents first.")

    overview = await _svc.generate_overview(
        subject_id=subject_id,
        subject_name=subj.get("name", subject_id),
        doc_texts=doc_texts,
    )
    return overview


@router.delete("", status_code=204)
def delete_overview(subject_id: str):
    _svc.delete_overview(subject_id)
