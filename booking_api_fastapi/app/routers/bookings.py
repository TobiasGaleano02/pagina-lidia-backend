# app/routers/bookings.py
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, time, date as date_cls, timezone
from sqlalchemy import text
from app.db import get_db

router = APIRouter(prefix="/bookings", tags=["bookings"])

class BookingIn(BaseModel):
    service_id: int
    staff_id: int
    customer_name: str = Field(min_length=2)
    customer_phone: str | None = ""           # ← tolera vacío
    starts_at: datetime                        # ej: "2025-09-02T17:30:00-04:00"

class BookingOut(BaseModel):
    id: int
    service_id: int
    staff_id: int
    customer_name: str
    customer_phone: str
    starts_at: datetime
    ends_at: datetime
    price: int
    status: str

@router.post("", response_model=BookingOut)
def create_booking(payload: BookingIn, db=Depends(get_db)):
    # 0) Normalizar datetime: si viene con tz, pasarlo a hora local "naive"
    start = payload.starts_at
    if start.tzinfo is not None:
        start = start.astimezone().replace(tzinfo=None)

    # 1) Servicio (duración + precio)
    svc = db.execute(text("""
        SELECT id, duration_minutes, price
        FROM services
        WHERE id = :sid
    """), {"sid": payload.service_id}).mappings().first()
    if not svc:
        raise HTTPException(400, "Servicio inexistente")

    # 2) Calcular fin
    ends_at = start + timedelta(minutes=int(svc["duration_minutes"]))

    # 3) Solapamientos para el mismo staff (confirmed), SIN tsrange
    clash = db.execute(text("""
        SELECT 1
        FROM bookings
        WHERE staff_id = :staff_id
          AND status = 'confirmed'
          AND NOT (:end <= starts_at OR :start >= ends_at)
        LIMIT 1
    """), {"staff_id": payload.staff_id, "start": start, "end": ends_at}).first()
    if clash:
        raise HTTPException(409, "Ese horario ya fue tomado. Elegí otro.")

    # 4) Insertar
    try:
        row = db.execute(text("""
            INSERT INTO bookings
                (service_id, staff_id, customer_name, customer_phone, starts_at, ends_at, price, status)
            VALUES
                (:service_id, :staff_id, :name, :phone, :start, :end, :price, 'confirmed')
            RETURNING id, service_id, staff_id, customer_name, customer_phone, starts_at, ends_at, price, status
        """), {
            "service_id": payload.service_id,
            "staff_id": payload.staff_id,
            "name": payload.customer_name,
            "phone": payload.customer_phone or "",
            "start": start,
            "end": ends_at,
            "price": int(svc["price"]),
        }).mappings().first()
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"DB error: {e}")

    return row

# --------- Horarios disponibles ----------
@router.get("/available-slots")
def get_available_slots(
    service_id: int = Query(...),
    staff_id: int = Query(...),
    # compatibilidad: acepto 'date' o 'day'
    date: str | None = Query(None, description="YYYY-MM-DD"),
    day:  str | None = Query(None, description="YYYY-MM-DD"),
    db=Depends(get_db),
):
    if service_id is None:
        raise HTTPException(422, "Falta 'service_id'")

    # 1) fecha
    ds = date or day
    if not ds:
        raise HTTPException(422, "Debe enviar 'date' (YYYY-MM-DD).")
    try:
        day_date = datetime.strptime(ds, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(400, "Formato de fecha inválido. Usa YYYY-MM-DD")

    # 2) bloquear días pasados
    if day_date < date_cls.today():
        return []

    # 3) duración del servicio
    svc = db.execute(
        text("SELECT duration_minutes FROM services WHERE id = :sid"),
        {"sid": service_id},
    ).mappings().first()
    if not svc:
        raise HTTPException(404, "Servicio inexistente")
    duration = int(svc["duration_minutes"])
    service_delta = timedelta(minutes=duration)

    # 4) ventana laboral fija: 08:30–18:30 (último turno arranca como mucho 18:15)
    work_start = datetime.combine(day_date, time(8, 30))
    work_end   = datetime.combine(day_date, time(18, 30))

    # 5) reservas confirmadas que pisan esa ventana
    taken = db.execute(text("""
        SELECT starts_at, ends_at
        FROM bookings
        WHERE staff_id = :sid
          AND status = 'confirmed'
          AND starts_at < :work_end
          AND ends_at   > :work_start
    """), {"sid": staff_id, "work_start": work_start, "work_end": work_end}).mappings().all()

    def to_naive_local(dt: datetime) -> datetime:
        return dt.astimezone().replace(tzinfo=None) if dt.tzinfo is not None else dt

    taken_ranges = [(to_naive_local(r["starts_at"]), to_naive_local(r["ends_at"])) for r in taken]

    # 6) grilla: cada 15 minutos
    GRID = timedelta(minutes=15)
    now = datetime.now()
    cur = work_start

    # si es hoy, arrancar desde el próximo cuarto de hora
    if day_date == now.date():
        cur = max(cur, now.replace(second=0, microsecond=0))
        mod = cur.minute % 15
        if mod or cur.second or cur.microsecond:
            cur = cur.replace(second=0, microsecond=0) + timedelta(minutes=(15 - mod) if mod else 0)

    slots: list[str] = []
    while cur <= work_end:                                 # <= 18:30
        candidate_end = cur + service_delta                # para chequear solapes con reservas
        overlap = any(not (candidate_end <= s or e <= cur) for s, e in taken_ranges)
        if not overlap:
            slots.append(cur.strftime("%H:%M"))            # incluimos 18:30
        cur += GRID

    return slots

