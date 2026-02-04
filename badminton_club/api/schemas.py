from datetime import date, datetime
from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    username: str
    email: str | None = None
    phone_number: str | None = None
    is_active: bool

    model_config = {"from_attributes": True}


class LinkPhoneRequest(BaseModel):
    username: str
    phone_number: str


class LocationOut(BaseModel):
    id: int
    name: str
    address: str | None = None

    model_config = {"from_attributes": True}


class AvailabilityOut(BaseModel):
    id: int
    date: date
    time_slot: str
    location: LocationOut
    num_guests: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AddAvailabilityRequest(BaseModel):
    date: date
    time_slots: list[str]
    location_ids: list[int]
    num_guests: int = 0


class SessionMember(BaseModel):
    username: str
    num_guests: int


class SessionSlot(BaseModel):
    time_slot: str
    location: LocationOut
    members: list[SessionMember]


class SessionSummary(BaseModel):
    date: date
    total_interest: int
    slots: list[SessionSlot] | None = None
