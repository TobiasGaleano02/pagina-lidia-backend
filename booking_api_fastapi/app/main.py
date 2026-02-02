from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse

from app.routers import bookings, admin, catalog

app = FastAPI()

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
