from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Service, Staff

router = APIRouter(tags=["catalog"])

@router.get("/services")
def list_services(db: Session = Depends(get_db)):
    rows = (
        db.query(Service)
        .order_by(Service.category, Service.name)
        .all()
    )
    return [
        {
            "id": s.id,
            "category": s.category,
            "name": s.name,
            "description": s.description,
            "price": s.price,
            "duration_minutes": s.duration_minutes,
        }
        for s in rows
    ]

@router.get("/staff")
def list_staff(db: Session = Depends(get_db)):
    rows = (
        db.query(Staff)
        .filter(Staff.active == True)
        .order_by(Staff.full_name)
        .all()
    )
    return [
        {
            "id": x.id,
            "full_name": x.full_name,
            "phone": x.phone,
            "active": x.active,
            "timezone": x.timezone,
        }
        for x in rows
    ]
