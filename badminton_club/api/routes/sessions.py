from datetime import date, timedelta

from fastapi import APIRouter, HTTPException
from sqlalchemy import func

from badminton_club.database import db_session
from badminton_club.database.models import PlayRecommendation, User, Location
from badminton_club.api.schemas import (
    SessionSummary,
    SessionSlot,
    SessionMember,
    LocationOut,
)

router = APIRouter(tags=["sessions"])


@router.get("/sessions/upcoming", response_model=list[SessionSummary])
def get_upcoming_sessions():
    today = date.today()
    end_date = today + timedelta(days=14)

    rows = (
        db_session.query(
            PlayRecommendation.date,
            func.count(func.distinct(PlayRecommendation.user_id)).label("unique_users"),
            func.sum(PlayRecommendation.num_guests).label("total_guests"),
        )
        .filter(PlayRecommendation.date >= today, PlayRecommendation.date <= end_date)
        .group_by(PlayRecommendation.date)
        .order_by(PlayRecommendation.date)
        .all()
    )

    return [
        SessionSummary(
            date=row.date,
            total_interest=row.unique_users + (row.total_guests or 0),
        )
        for row in rows
    ]


@router.get("/sessions/{session_date}", response_model=SessionSummary)
def get_session_detail(session_date: date):
    recs = (
        db_session.query(PlayRecommendation)
        .join(User)
        .join(Location)
        .filter(PlayRecommendation.date == session_date)
        .all()
    )

    if not recs:
        raise HTTPException(status_code=404, detail="No sessions found for this date")

    slots: dict[tuple[str, int], SessionSlot] = {}
    for rec in recs:
        key = (rec.time_slot, rec.location_id)
        if key not in slots:
            slots[key] = SessionSlot(
                time_slot=rec.time_slot,
                location=LocationOut.model_validate(rec.location),
                members=[],
            )
        slots[key].members.append(
            SessionMember(username=rec.user.username, num_guests=rec.num_guests)
        )

    unique_users = len({r.user_id for r in recs})
    total_guests = sum(r.num_guests for r in recs)

    return SessionSummary(
        date=session_date,
        total_interest=unique_users + total_guests,
        slots=list(slots.values()),
    )
