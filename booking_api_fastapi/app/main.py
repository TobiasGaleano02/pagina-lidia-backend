from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse

from app.routers import bookings, admin, catalog
from app.db import engine
from app.models import Base

app = FastAPI()

# ✅ CORS: una sola vez, con tu dominio de Vercel + previews
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://pagina-lidia-frontend.vercel.app",
    ],
    allow_origin_regex=r"^https://.*\.vercel\.app$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ crea tablas si no existen
Base.metadata.create_all(bind=engine)

# Routers
app.include_router(catalog.router)
app.include_router(bookings.router)
app.include_router(admin.router)

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/availability")
def availability_alias(request: Request):
    return RedirectResponse(
        url=f"/bookings/available-slots?{request.url.query}",
        status_code=307,
    )

@app.post("/__seed")
def run_seed():
    from app.seed import main as seed_main
    seed_main()
    return {"ok": True}