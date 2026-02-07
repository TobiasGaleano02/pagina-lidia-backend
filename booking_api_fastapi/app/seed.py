# booking_api_fastapi/app/seed.py
from __future__ import annotations

from datetime import time
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Service, Staff, StaffSchedule


def ensure_service(db: Session, *, category: str, name: str, description: str, price: int, duration_minutes: int):
    exists = (
        db.query(Service)
        .filter(Service.category == category, Service.name == name)
        .first()
    )
    if exists:
        return

    service = Service(
        category=category,
        name=name,
        description=description,
        price=price,
        duration_minutes=duration_minutes,
    )
    db.add(service)
    db.flush()  # ✅ fuerza INSERT ahora y obtiene id si hace falta


def ensure_staff(db: Session, *, full_name: str, phone: str | None, active: bool = True, timezone: str = "America/Asuncion") -> Staff:
    staff = db.query(Staff).filter(Staff.full_name == full_name).first()
    if staff:
        # Si querés que actualice teléfono/activo en cada seed, descomentá:
        # staff.phone = phone
        # staff.active = active
        # staff.timezone = timezone
        return staff

    staff = Staff(
        full_name=full_name,
        phone=phone,
        active=active,
        timezone=timezone,
    )
    db.add(staff)
    db.flush()  # obtiene staff.id sin commit
    return staff


def ensure_schedule(
    db: Session,
    *,
    staff_id: int,
    day_of_week: int,
    start_time: time,
    end_time: time,
    break_minutes: int = 0,
) -> None:
    exists = (
        db.query(StaffSchedule)
        .filter(
            StaffSchedule.staff_id == staff_id,
            StaffSchedule.day_of_week == day_of_week,
            StaffSchedule.start_time == start_time,
            StaffSchedule.end_time == end_time,
        )
        .first()
    )
    if exists:
        return

    db.add(
        StaffSchedule(
            staff_id=staff_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            break_minutes=break_minutes,
        )
    )


def main() -> None:
    db = SessionLocal()
    try:
        # =========================
        # 1) SERVICES (EDITÁ A TU GUSTO)
        # =========================
        services = [
            # Micropigmentación Cejas
            ("Micropigmentación - Cejas", "Microblading", "Técnica pelo a pelo para un resultado natural.", 800000, 120),
            ("Micropigmentación - Cejas", "Shading", "Efecto sombreado suave para cejas definidas.", 800000, 120),
            ("Micropigmentación - Cejas", "Nanoblading", "Pelo a pelo ultra fino, mayor realismo.", 850000, 150),
            ("Micropigmentación - Cejas", "Micro Híbrida", "Combinación pelo a pelo + sombreado.", 850000, 150),

            # Micropigmentación Labios
            ("Micropigmentación - Labios", "Micro Lips", "Color uniforme y definición natural.", 990000, 150),
            ("Micropigmentación - Labios", "Neutralización de labios", "Corrige tonos oscuros y empareja color.", 990000, 150),
            ("Micropigmentación - Labios", "Magic Lips", "Efecto hidratado y luminoso.", 990000, 150),

            # Micropigmentación Ojos
            ("Micropigmentación - Ojos", "Classic Eyeliner", "Delineado clásico para mirada marcada.", 700000, 120),
            ("Micropigmentación - Ojos", "Soft Liner", "Delineado difuminado, súper natural.", 700000, 120),

            # Complementarios
            ("Mirada Perfecta", "Lifting de pestañas", "Eleva y curva tus pestañas naturales.", 180000, 60),
            ("Mirada Perfecta", "Brow Lamination", "Ordena y fija cejas, efecto peinado.", 200000, 60),
            ("Mirada Perfecta", "Diseño de cejas + Henna", "Diseño + tinte para cejas más definidas.", 150000, 45),
            ("Mirada Perfecta", "Extensión de pestañas (clásicas)", "Volumen natural, elegante.", 250000, 120),

            # Faciales / labios
            ("Faciales", "BB Glow", "Efecto piel luminosa y uniforme.", 250000, 60),
            ("Faciales", "Hollywood Peel", "Limpieza profunda + glow.", 300000, 60),
            ("Labios", "Hidra Lips", "Hidratación y efecto volumen.", 180000, 45),

            # Depilación
            ("Depilación Láser", "Depilación láser - Zona chica", "Axilas/bozo/mentón (según disponibilidad).", 150000, 30),
            ("Depilación Láser", "Depilación láser - Zona mediana", "Brazos/abdomen (según disponibilidad).", 250000, 45),
            ("Depilación Láser", "Depilación láser - Zona grande", "Piernas completas/espalda (según disponibilidad).", 350000, 60),
        ]

        for cat, name, desc, price, dur in services:
            ensure_service(db, category=cat, name=name, description=desc, price=price, duration_minutes=dur)

        # =========================
        # 2) STAFF (EDITÁ NOMBRES Y TELÉFONOS)
        # =========================
        # ⚠️ Cambiá estos 3 por tus nombres reales.
        staff_list = [
            ("Lidia Imlach", None, True),
            ("Staff 1", None, True),
            ("Staff 2", None, True),
        ]

        staff_objs: list[Staff] = []
        for full_name, phone, active in staff_list:
            staff_objs.append(ensure_staff(db, full_name=full_name, phone=phone, active=active))

        
        # =========================
        # 3) HORARIOS (0=Dom ... 6=Sáb)
        # =========================
        # Lunes a Viernes: 09:00-18:00 con break 60
        # Sábado: 09:00-13:00 sin break
        for st in staff_objs:
            # Lun(1) a Vie(5)
            for dow in range(1, 6):
                ensure_schedule(
                    db,
                    staff_id=st.id,
                    day_of_week=dow,
                    start_time=time(9, 0),
                    end_time=time(18, 0),
                    break_minutes=60,
                )
            # Sáb(6)
            ensure_schedule(
                db,
                staff_id=st.id,
                day_of_week=6,
                start_time=time(9, 0),
                end_time=time(13, 0),
                break_minutes=0,
            )

        db.commit()
        print("✅ Seed OK: services + staff + schedules listos.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()