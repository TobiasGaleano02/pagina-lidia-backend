# app/routers/appointments.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Appointment, Service, Staff
from app.schemas import AppointmentCreate  # Si no existe, ver el fallback más abajo
from app.utils.time import parse_local_datetime

router = APIRouter(prefix="/appointments", tags=["appointments"])

# ---- Fallback si tu schemas.py no tiene AppointmentCreate:
# from pydantic import BaseModel
# class AppointmentCreate(BaseModel):
#     staff_id: int | None = None
#     service_id: int
#     client_name: str
#     client_phone: str | None = None
#     start_local: str  # "YYYY-MM-DD HH:MM"

@router.post("/")
def create_appointment(appt: AppointmentCreate, db: Session = Depends(get_db)):
    # Buscar servicio para conocer la duración
    svc = db.get(Service, appt.service_id)
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")

    # Convertir el start_local a datetime (tratado como UTC simple por ahora)
    start_utc = parse_local_datetime(appt.start_local)
    end_utc = start_utc + timedelta(minutes=svc.duration_minutes or 0)

    new_appt = Appointment(
        service_id=appt.service_id,
        staff_id=appt.staff_id,
        client_name=appt.client_name.strip(),
        client_phone=(appt.client_phone or None),
        start_utc=start_utc,
        end_utc=end_utc,
        status="booked",
        notes=None,
    )
    db.add(new_appt)
    db.commit()
    db.refresh(new_appt)
    return {
        "id": new_appt.id,
        "service_id": new_appt.service_id,
        "staff_id": new_appt.staff_id,
        "client_name": new_appt.client_name,
        "client_phone": new_appt.client_phone,
        "status": new_appt.status,
        "start_utc": new_appt.start_utc.isoformat(),
        "end_utc": new_appt.end_utc.isoformat() if new_appt.end_utc else None,
    }