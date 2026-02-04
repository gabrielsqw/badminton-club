from datetime import date

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from badminton_club.database import db_session
from badminton_club.database.models import PlayRecommendation, User, Location
from badminton_club.api.schemas import AvailabilityOut, AddAvailabilityRequest

router = APIRouter(tags=["availability"])


@router.get("/users/{user_id}/availability", response_model=list[AvailabilityOut])
def get_user_availability(user_id: int):
    user = (
        db_session.query(User)
        .filter(User.id == user_id, User.is_active.is_(True))
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    recs = (
        db_session.query(PlayRecommendation)
        .join(Location)
        .filter(PlayRecommendation.user_id == user_id)
        .order_by(PlayRecommendation.date, PlayRecommendation.time_slot)
        .all()
    )
    return recs


@router.post("/users/{user_id}/availability", response_model=list[AvailabilityOut])
def add_availability(user_id: int, req: AddAvailabilityRequest):
    user = (
        db_session.query(User)
        .filter(User.id == user_id, User.is_active.is_(True))
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    locations = (
        db_session.query(Location)
        .filter(Location.id.in_(req.location_ids), Location.is_active.is_(True))
        .all()
    )
    if len(locations) != len(req.location_ids):
        raise HTTPException(status_code=400, detail="One or more locations not found")

    created = []
    for time_slot in req.time_slots:
        for loc in locations:
            existing = (
                db_session.query(PlayRecommendation)
                .filter(
                    PlayRecommendation.user_id == user_id,
                    PlayRecommendation.date == req.date,
                    PlayRecommendation.time_slot == time_slot,
                    PlayRecommendation.location_id == loc.id,
                )
                .first()
            )

            if existing:
                existing.num_guests = req.num_guests
                created.append(existing)
            else:
                rec = PlayRecommendation(
                    user_id=user_id,
                    location_id=loc.id,
                    date=req.date,
                    time_slot=time_slot,
                    num_guests=req.num_guests,
                )
                db_session.add(rec)
                created.append(rec)

    try:
        db_session.commit()
        for rec in created:
            db_session.refresh(rec)
    except SQLAlchemyError:
        db_session.rollback()
        raise HTTPException(status_code=500, detail="Failed to save availability")

    return created


@router.delete("/users/{user_id}/availability/{avail_date}")
def delete_availability(user_id: int, avail_date: date):
    recs = (
        db_session.query(PlayRecommendation)
        .filter(
            PlayRecommendation.user_id == user_id,
            PlayRecommendation.date == avail_date,
        )
        .all()
    )

    if not recs:
        raise HTTPException(
            status_code=404, detail="No availability found for this date"
        )

    for rec in recs:
        db_session.delete(rec)

    try:
        db_session.commit()
    except SQLAlchemyError:
        db_session.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete availability")

    return {"deleted": len(recs)}
