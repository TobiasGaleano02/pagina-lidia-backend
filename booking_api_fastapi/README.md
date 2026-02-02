# Salon Booking API (FastAPI)

API mínima para catálogo de servicios, staff, disponibilidad y reservas con PostgreSQL.

## 1) Requisitos
- Python 3.11+
- PostgreSQL con la base `salon_booking` y las tablas creadas (ya cargaste `services`, `staff`, `staff_schedules`, `blackouts`, `appointments` con los .sql que te di).
- Crear y completar `.env` (copiar de `.env.example`).

## 2) Instalación
```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell
pip install -r requirements.txt
```

## 3) Configuración
Crea un archivo `.env` en la raíz con:
```
DATABASE_URL=postgresql+psycopg2://postgres:your_password@localhost:5432/salon_booking
APP_TIMEZONE=America/Asuncion
DEFAULT_BUFFER_MIN=10
```

## 4) Ejecutar
```bash
uvicorn app.main:app --reload --port 8000
```

## 5) Endpoints principales
- GET `http://127.0.0.1:8000/health`
- GET `http://127.0.0.1:8000/services`
- GET `http://127.0.0.1:8000/staff`
- GET `http://127.0.0.1:8000/staff/{staff_id}/schedules`
- GET `http://127.0.0.1:8000/availability?service_id=1&day=2025-08-25`
- POST `http://127.0.0.1:8000/appointments`
  ```json
  {
    "staff_id": 1,
    "service_id": 1,
    "client_name": "Cliente Demo",
    "client_phone": "+595...",
    "start_local": "2025-08-26 15:00"
  }
  ```
- GET `http://127.0.0.1:8000/appointments/day?date_local=2025-08-26&staff_id=1`

> **Notas**
> - La disponibilidad usa `duration_minutes` del servicio + `DEFAULT_BUFFER_MIN` para separar turnos (configurable en `.env`).
> - La colisión de turnos está protegida por la **constraint EXCLUDE** en PostgreSQL. Si intentás reservar un turno ocupado, el API devuelve 409.
> - Los horarios y blackouts se consideran al calcular disponibilidad.

## 6) Próximo paso (Frontend)
Crear un link/front simple (Streamlit o React) que consuma `/services`, `/availability` y cree reservas via `/appointments`.
