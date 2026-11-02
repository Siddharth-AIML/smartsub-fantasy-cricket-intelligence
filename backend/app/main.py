from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import Base, sync_engine, SyncSessionLocal
from app.services.seed_data import seed_database
from app.routers import matches, fantasy_teams, substitutions, ai, rules

def init_app():
    # Initialize SQLite or PostgreSQL tables
    Base.metadata.create_all(bind=sync_engine)
    # Seed canonical demo data (CSK vs MI)
    db = SyncSessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

# Initialize upon module load
init_app()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Deterministic Substitution Engine with AI Explainability for Fantasy Cricket"
)

# Enable CORS for local Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(matches.router)
app.include_router(fantasy_teams.router)
app.include_router(substitutions.router)
app.include_router(ai.router)
app.include_router(rules.router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database_url_dialect": settings.DATABASE_URL.split(":")[0],
        "has_gemini_api_key": bool(settings.GEMINI_API_KEY),
        "data_provenance": settings.DATA_PROVENANCE_TAG
    }

# Mount static frontend build if it exists
import os
from fastapi.staticfiles import StaticFiles

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend_dist")

