from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from ..db import get_db
from .. import models, schemas
from ..config import APP_TIMEZONE, DEFAULT_BUFFER_MIN
from ..utils.time import local_date_bounds_utc, utc_to_local, combine_date_time_local, iter_range

router = APIRouter(prefix="/availability", tags=["availability"])

@router.get("", response_model=list[schemas.AvailabilityPerStaff])
def availability(
    service_id: int = Query(..., description="ID del servicio"),
    day: date = Query(..., description="Fecha local YYYY-MM-DD"),
    staff_id: int | None = Query(None, description="Filtrar por staff (opcional)"),
    db: Session = Depends(get_db),
):
    service = db.get(models.Service, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    duration = service.duration_minutes
    buffer_min = DEFAULT_BUFFER_MIN

    staff_q = db.query(models.Staff).filter(models.Staff.active == True)
    if staff_id:
        staff_q = staff_q.filter(models.Staff.id == staff_id)
    staffs = staff_q.all()
    if not staffs:
        return []

    day_start_utc, day_end_utc = local_date_bounds_utc(day, APP_TIMEZONE)

    results: list[schemas.AvailabilityPerStaff] = []
    for st in staffs:
        # convertir: lunes=0..domingo=6  a esquema 0=domingo..6=sábado
        dow = (day.weekday() + 1) % 7
        schedules = (db.query(models.StaffSchedule)
                       .filter(models.StaffSchedule.staff_id == st.id,
                               models.StaffSchedule.day_of_week == dow)
                       .all())

        if not schedules:
            results.append(schemas.AvailabilityPerStaff(
                staff_id=st.id, staff_name=st.full_name, date_local=str(day),
                service_id=service_id, slots=[]
            ))
            continue

        appts = (db.query(models.Appointment)
                   .filter(models.Appointment.staff_id == st.id,
                           models.Appointment.starts_at < day_end_utc,
                           models.Appointment.ends_at > day_start_utc)
                   .all())
        blks = (db.query(models.Blackout)
                   .filter(models.Blackout.staff_id == st.id,
                           models.Blackout.starts_at < day_end_utc,
                           models.Blackout.ends_at > day_start_utc)
                   .all())

        busy_local: list[tuple[datetime, datetime]] = []
        for a in appts:
            busy_local.append((
                utc_to_local(a.starts_at, APP_TIMEZONE),
                utc_to_local(a.ends_at,   APP_TIMEZONE),
            ))
        for b in blks:
            busy_local.append((
                utc_to_local(b.starts_at, APP_TIMEZONE),
                utc_to_local(b.ends_at,   APP_TIMEZONE),
            ))

        def overlaps(a_start, a_end, b_start, b_end):
            return a_start < b_end and a_end > b_start

        out_slots: list[schemas.SlotOut] = []
        for sch in schedules:
            start_dt = combine_date_time_local(day, sch.start_time, APP_TIMEZONE)
            end_dt   = combine_date_time_local(day, sch.end_time,   APP_TIMEZONE)

            step = 5  # minutos
            for cand in iter_range(start_dt, end_dt, step):
                cand_end = cand + timedelta(minutes=duration + buffer_min)
                if cand_end > end_dt:
                    break
                if any(overlaps(cand, cand_end, b_s, b_e) for (b_s, b_e) in busy_local):
                    continue
                out_slots.append(schemas.SlotOut(time_local=cand.strftime("%H:%M")))

        # dedup
        seen, unique = set(), []
        for s in out_slots:
            if s.time_local not in seen:
                seen.add(s.time_local)
                unique.append(s)

        results.append(schemas.AvailabilityPerStaff(
            staff_id=st.id,
            staff_name=st.full_name,
            date_local=str(day),
            service_id=service_id,
            slots=unique
        ))

    return results
