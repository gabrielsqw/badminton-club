from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from badminton_club.database import db_session
from badminton_club.database.models import User
from badminton_club.api.schemas import UserOut, LinkPhoneRequest

router = APIRouter(tags=["users"])


@router.get("/users/by-phone/{phone}", response_model=UserOut)
def get_user_by_phone(phone: str):
    user = (
        db_session.query(User)
        .filter(User.phone_number == phone, User.is_active.is_(True))
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=404, detail="User not found for this phone number"
        )
    return user


@router.post("/users/link-phone", response_model=UserOut)
def link_phone(req: LinkPhoneRequest):
    user = (
        db_session.query(User)
        .filter(User.username == req.username, User.is_active.is_(True))
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="Username not found")

    existing = (
        db_session.query(User).filter(User.phone_number == req.phone_number).first()
    )
    if existing and existing.id != user.id:
        raise HTTPException(
            status_code=409, detail="Phone number already linked to another account"
        )

    user.phone_number = req.phone_number
    try:
        db_session.commit()
    except SQLAlchemyError:
        db_session.rollback()
        raise HTTPException(status_code=500, detail="Failed to link phone number")
    return user
