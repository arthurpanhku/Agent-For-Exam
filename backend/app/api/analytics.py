"""Analytics API routes for the study dashboard."""
from __future__ import annotations

from fastapi import APIRouter

from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

_svc = AnalyticsService()


@router.get("/global")
def global_stats():
    return _svc.global_stats()


@router.get("/subjects/{subject_id}")
def subject_stats(subject_id: str):
    return _svc.subject_stats(subject_id)
