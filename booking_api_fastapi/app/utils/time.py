# app/utils/time.py
from __future__ import annotations
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

# ---- helpers básicos de parseo ----
def _ensure_date(d: date | str) -> date:
    if isinstance(d, date):
        return d
    return datetime.strptime(d, "%Y-%m-%d").date()

def _ensure_time(t: time | str) -> time:
    if isinstance(t, time):
        return t
    # admite "HH:MM" o "HH:MM:SS"
    parts = [int(x) for x in t.split(":")]
    if len(parts) == 2:
        hh, mm = parts
        ss = 0
    else:
        hh, mm, ss = parts
    return time(hour=hh, minute=mm, second=ss)

# ---- conversión zona horaria ----
def local_date_bounds_utc(day: date | str, tz_name: str) -> tuple[datetime, datetime]:
    """
    Devuelve (inicio_utc, fin_utc) para el día local indicado.
    start = YYYY-MM-DD 00:00:00 local
    end   = YYYY-MM-DD 00:00:00 del día siguiente local
    """
    d = _ensure_date(day)
    tz = ZoneInfo(tz_name)

    start_local = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=tz)
    end_local = start_local + timedelta(days=1)

    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)
    return start_utc, end_utc

def combine_date_time_local(day: date | str, hhmm: time | str, tz_name: str) -> datetime:
    d = _ensure_date(day)
    t = _ensure_time(hhmm)
    tz = ZoneInfo(tz_name)
    return datetime(d.year, d.month, d.day, t.hour, t.minute, t.second, tzinfo=tz)

def utc_to_local(dt_utc: datetime, tz_name: str) -> datetime:
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    return dt_utc.astimezone(ZoneInfo(tz_name))

def local_to_utc(dt_local: datetime, tz_name: str) -> datetime:
    if dt_local.tzinfo is None:
        dt_local = dt_local.replace(tzinfo=ZoneInfo(tz_name))
    return dt_local.astimezone(timezone.utc)

# ---- iterador de rangos ----
def iter_range(start: datetime, end: datetime, step_minutes: int):
    """Genera instantes [start, end) cada step_minutes."""
    cur = start
    delta = timedelta(minutes=step_minutes)
    while cur < end:
        yield cur
        cur = cur + delta
        
def parse_local_datetime(s: str, tz_name: str) -> datetime:
    """
    Convierte un string 'YYYY-MM-DD HH:MM' en datetime con zona horaria local.
    """
    d = datetime.strptime(s, "%Y-%m-%d %H:%M")
    tz = ZoneInfo(tz_name)
    return d.replace(tzinfo=tz)