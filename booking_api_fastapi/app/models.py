from sqlalchemy import (
    Column, Integer, String, Boolean, Text, ForeignKey, CheckConstraint,
    Time, SmallInteger, DateTime
)
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import relationship
from .db import Base
from sqlalchemy.sql import func


class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True)
    category = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text)
    price = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, nullable=False)

    appointments = relationship("Appointment", back_populates="service")


class Staff(Base):
    __tablename__ = "staff"
    id = Column(Integer, primary_key=True)
    full_name = Column(Text, nullable=False)
    phone = Column(Text)
    active = Column(Boolean, nullable=False, default=True)
    timezone = Column(Text, nullable=False, default="America/Asuncion")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    appointments = relationship("Appointment", back_populates="staff")

class StaffSchedule(Base):
    __tablename__ = "staff_schedules"
    id = Column(Integer, primary_key=True)
    staff_id = Column(Integer, ForeignKey("staff.id", ondelete="CASCADE"), nullable=False)
    day_of_week = Column(SmallInteger, nullable=False)  # 0=domingo...6=sábado
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    break_minutes = Column(Integer, nullable=False, default=0)

class Blackout(Base):
    __tablename__ = "blackouts"
    id = Column(Integer, primary_key=True)
    staff_id = Column(Integer, ForeignKey("staff.id", ondelete="CASCADE"), nullable=False)
    reason = Column(Text)
    starts_at = Column(TIMESTAMP(timezone=True), nullable=False)
    ends_at = Column(TIMESTAMP(timezone=True), nullable=False)

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True)
    staff_id = Column(Integer, ForeignKey("staff.id", ondelete="RESTRICT"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="RESTRICT"), nullable=False)
    client_name = Column(Text, nullable=False)
    client_phone = Column(Text)
    status = Column(Text, nullable=False, default="confirmed")
    starts_at = Column(TIMESTAMP(timezone=True), nullable=False)
    ends_at = Column(TIMESTAMP(timezone=True), nullable=False)
    notes = Column(Text)

    staff = relationship("Staff", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")