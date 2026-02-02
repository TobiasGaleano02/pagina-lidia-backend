from pydantic import BaseModel
from typing import Optional, List

# ---------- Services ----------
class ServiceOut(BaseModel):
    id: int
    category: str
    name: str
    description: Optional[str] = None
    price: int
    duration_minutes: int
    class Config: from_attributes = True

# ---------- Staff ----------
class StaffOut(BaseModel):
    id: int
    full_name: str
    phone: Optional[str] = None
    active: bool
    class Config: from_attributes = True

class StaffScheduleOut(BaseModel):
    id: int
    day_of_week: int
    start_time: str
    end_time: str
    break_minutes: int
    class Config: from_attributes = True

# ---------- Availability ----------
class SlotOut(BaseModel):
    time_local: str  # 'HH:MM'

class AvailabilityPerStaff(BaseModel):
    staff_id: int
    staff_name: str
    date_local: str  # YYYY-MM-DD
    service_id: int
    slots: List[SlotOut]

# ---------- Appointments ----------
class AppointmentCreate(BaseModel):
    staff_id: int
    service_id: int
    client_name: str
    client_phone: Optional[str] = None
    start_local: str  # 'YYYY-MM-DD HH:MM'

class AppointmentOut(BaseModel):
    id: int
    staff_id: int
    service_id: int
    client_name: str
    client_phone: Optional[str]
    status: str
    starts_at: str
    ends_at: str
    notes: Optional[str] = None
    class Config: from_attributes = True

# ---------- Admin patch ----------
class AppointmentPatch(BaseModel):
    status: Optional[str] = None
    start_local: Optional[str] = None  # "YYYY-MM-DD HH:MM"
    staff_id: Optional[int] = None
    notes: Optional[str] = None
