from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.seed import seed_master_data
from app.routers import auth, items, production, sales, reports

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Order-to-Audit System for a Small Food Manufacturer (NIT Tiruchirappalli Internship Task)"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(items.router, prefix=settings.API_V1_STR)
app.include_router(production.router, prefix=settings.API_V1_STR)
app.include_router(sales.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def startup_populate():
    db = SessionLocal()
    try:
        seed_master_data(db)
    finally:
        db.close()

@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "factory": {
            "name": "South Indian Snacks Manufacturer",
            "state": settings.FACTORY_STATE,
            "state_code": settings.FACTORY_STATE_CODE,
            "gstin": settings.FACTORY_GSTIN
        },
        "status": "online"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}
