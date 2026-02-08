from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from app.routers import bookings, admin, catalog
from app.db import engine
from app.models import Base

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:5173",  # Vite
    "http://127.0.0.1:5173",
    "https://pagina-lidia-frontend.vercel.app",
    # después agregamos tu dominio de producción (Vercel/Netlify) cuando lo tengas
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://lidia-booking-frontend.vercel.app",
        "http://localhost:5173",
    ],
    allow_origin_regex=r"^https://.*\.vercel\.app$",  # ← anclado
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        status_code=307
    )


# ⚠️ TEMPORAL: correr seed en producción UNA VEZ
from app.seed import main as seed_main

seed_main()