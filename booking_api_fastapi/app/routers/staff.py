from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas

router = APIRouter(prefix="/staff", tags=["staff"])

@router.get("", response_model=list[schemas.StaffOut])
def list_staff(db: Session = Depends(get_db)):
    q = db.query(models.Staff).filter(models.Staff.active == True).order_by(models.Staff.full_name)
    return q.all()

@router.get("/{staff_id}/schedules", response_model=list[schemas.StaffScheduleOut])
def staff_schedules(staff_id: int, db: Session = Depends(get_db)):
    q = (db.query(models.StaffSchedule)
           .filter(models.StaffSchedule.staff_id == staff_id)
           .order_by(models.StaffSchedule.day_of_week, models.StaffSchedule.start_time))
    return q.all()
