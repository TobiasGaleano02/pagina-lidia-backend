# app/routers/admin.py
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import text
from typing import Optional
import os
from datetime import datetime, timedelta, date as date_cls

from app.db import get_db

router = APIRouter(prefix="/admin", tags=["admin"])

# --- Auth simple por header ---
def admin_guard(x_admin_token: Optional[str] = Header(None)):
    # Usá ADMIN_TOKEN en el .env del backend. Si no está, no se exige (dev).
    expected = os.getenv("ADMIN_TOKEN", "")
    if expected and x_admin_token != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

def parse_day(s: str) -> date_cls:
    return datetime.strptime(s, "%Y-%m-%d").date()

# ---------- LISTADO ----------
@router.get("/appointments")
def admin_list_appointments(
    date_from: str = Query(..., description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    staff_id: Optional[int] = None,
    status: Optional[str] = None,
    db = Depends(get_db),
    _: bool = Depends(admin_guard),
):
    # Rango [from, to)
    d_from = parse_day(date_from)
    d_to   = parse_day(date_to) if date_to else d_from
    start  = datetime.combine(d_from, datetime.min.time())
    end    = datetime.combine(d_to + timedelta(days=1), datetime.min.time())

    where = [
        "b.starts_at >= :start",
        "b.starts_at <  :end",
    ]
    params = {"start": start, "end": end}

    if staff_id:
        where.append("b.staff_id = :staff_id")
        params["staff_id"] = staff_id
    if status:
        where.append("b.status = :status")
        params["status"] = status

    sql = f"""
    SELECT
      b.id,
      b.service_id,
      s.name           AS service_name,
      b.staff_id,
      st.full_name     AS staff_name,
      b.customer_name  AS client_name,
      b.customer_phone AS client_phone,
      b.status,
      b.starts_at      AS start_utc,
      b.ends_at        AS end_utc
    FROM bookings b
    LEFT JOIN services s ON s.id = b.service_id
    LEFT JOIN staff    st ON st.id = b.staff_id
    WHERE {" AND ".join(where)}
    ORDER BY b.starts_at
    """
    rows = db.execute(text(sql), params).mappings().all()
    # El panel espera lista de dicts
    return [dict(r) for r in rows]

# ---------- PATCH (confirmar / cancelar / reprogramar / reasignar) ----------
from pydantic import BaseModel

class AppointmentPatch(BaseModel):
    status: Optional[str] = None
    start_local: Optional[str] = None   # "YYYY-MM-DD HH:MM" en hora local
    staff_id: Optional[int] = None
    # notes opcional: tu tabla bookings no tiene columna notes, por eso lo omito

@router.patch("/appointments/{appt_id}")
def patch_appointment(
    appt_id: int,
    p: AppointmentPatch,
    db = Depends(get_db),
    _: bool = Depends(admin_guard),
):
    # Traer booking + duración del servicio
    row = db.execute(text("""
        SELECT b.*, s.duration_minutes
        FROM bookings b
        JOIN services s ON s.id = b.service_id
        WHERE b.id = :id
    """), {"id": appt_id}).mappings().first()
    if not row:
        raise HTTPException(404, "Appointment not found")

    new_status  = p.status
    new_staff   = p.staff_id
    new_start   = None
    new_end     = None

    if p.start_local:
        try:
            # Interpretamos como hora local "naive"
            new_start = datetime.strptime(p.start_local, "%Y-%m-%d %H:%M")
        except ValueError:
            raise HTTPException(400, "start_local debe tener formato 'YYYY-MM-DD HH:MM'")
        dur = int(row["duration_minutes"] or 0)
        new_end = new_start + timedelta(minutes=dur)

        # Chequear solapamiento si se cambia hora o staff
        check_staff = new_staff if new_staff is not None else row["staff_id"]
        clash = db.execute(text("""
            SELECT 1
            FROM bookings
            WHERE staff_id = :staff_id
              AND id <> :id
              AND status = 'confirmed'
              AND NOT (:end <= starts_at OR :start >= ends_at)
            LIMIT 1
        """), {"staff_id": check_staff, "id": appt_id, "start": new_start, "end": new_end}).first()
        if clash:
            raise HTTPException(409, "El nuevo horario se solapa con otra reserva confirmada.")

    # Armar UPDATE dinámico
    sets = []
    params = {"id": appt_id}
    if new_status is not None:
        sets.append("status = :status")
        params["status"] = new_status
    if new_staff is not None:
        sets.append("staff_id = :staff_id")
        params["staff_id"] = new_staff
    if new_start is not None and new_end is not None:
        sets.append("starts_at = :start")
        sets.append("ends_at   = :end")
        params["start"] = new_start
        params["end"]   = new_end

    if not sets:
        # Nada para actualizar
        return {"ok": True}

    db.execute(text(f"""
        UPDATE bookings
        SET {", ".join(sets)}
        WHERE id = :id
    """), params)
    db.commit()

    # Devolver el registro actualizado en el mismo formato del listado
    updated = db.execute(text("""
        SELECT
          b.id,
          b.service_id,
          s.name           AS service_name,
          b.staff_id,
          st.full_name     AS staff_name,
          b.customer_name  AS client_name,
          b.customer_phone AS client_phone,
          b.status,
          b.starts_at      AS start_utc,
          b.ends_at        AS end_utc
        FROM bookings b
        LEFT JOIN services s ON s.id = b.service_id
        LEFT JOIN staff    st ON st.id = b.staff_id
        WHERE b.id = :id
    """), {"id": appt_id}).mappings().first()

    return {"ok": True, "appointment": dict(updated) if updated else None}
