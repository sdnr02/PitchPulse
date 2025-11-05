import redis
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends, HTTPException

from core.database import db_manager
from core.dependencies import get_db, get_redis

# Initializing the FastAPI app
app = FastAPI(
    title="PitchPulse API",
    description="The backend API for the PitchPulse cricket tournament management platform.",
    version="0.1.0 (Pilot)"
)

@app.get("/", tags=["Root"])
async def read_root():
    """
    A simple root endpoint to confirm the API is running.
    """
    return {"message": "Welcome to the PitchPulse API!"}

@app.get("/health", tags=["Health Check"])
async def health_check(
    db: Session = Depends(get_db), 
    redis_client: redis.Redis = Depends(get_redis)
):
    """
    Performs a health check on the database and Redis connections.
    """
    try:
        # Check PostgreSQL connection
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = "error"
        raise HTTPException(status_code=503, detail=f"Database connection error: {e}")

    try:
        # Check Redis connection
        redis_client.ping()
        redis_status = "ok"
    except Exception as e:
        redis_status = "error"
        raise HTTPException(status_code=503, detail=f"Redis connection error: {e}")

    return {
        "database_status": db_status,
        "redis_status": redis_status,
        "timestamp": "2025-10-08T13:41:04+05:30"
    }