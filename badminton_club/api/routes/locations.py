from fastapi import APIRouter

from badminton_club.database import db_session
from badminton_club.database.models import Location
from badminton_club.api.schemas import LocationOut

router = APIRouter(tags=["locations"])


@router.get("/locations", response_model=list[LocationOut])
def get_locations():
    locations = (
        db_session.query(Location)
        .filter(Location.is_active.is_(True))
        .order_by(Location.name)
        .all()
    )
    return locations
