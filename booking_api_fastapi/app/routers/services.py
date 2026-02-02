from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas

router = APIRouter(prefix="/services", tags=["services"])

@router.get("", response_model=list[schemas.ServiceOut])
def list_services(db: Session = Depends(get_db)):
    q = db.query(models.Service).order_by(models.Service.category, models.Service.name)
    return q.all()
