from typing import List
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Depends, Request

from app.core.database import get_redis
from app.core.middleware import log_requests
from app.core.logging_config import setup_logging
from app.core.database import SessionLocal, get_db
from app.models.match import Match, Tournament, Team
from app.services.scoring_service import ScoringService

from app.schemas.match_schemas import (
    TournamentCreate,
    TeamCreate,
    MatchCreate,
    MatchInitialize,
    BallEvent,
    MatchResponse,
    TournamentResponse,
    TeamResponse
)

import logging

setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # On Startup: this runs before app starts accepting requests
    logger.info("PitchPulse API starting up...")
    logger.info("Database connection initializing...")
    logger.info("Redis connection initializing...")
    logger.info("API ready to accept requests")
    
    yield  # The App runs here
    
    # Shutdown: runs when app is stopping (optional)
    logger.info("PitchPulse API shutting down...")

# Initializing the app object
app = FastAPI(
    title="PitchPulse API",
    description="Real-time cricket scoring API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"], # Allow all HTTP methods
    allow_headers=["*"] # Allowing all headers
)

app.middleware("http")(log_requests)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to catch all unhandled exceptions"""
    # Logging the error with full details
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Returning a JSON error response
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "path": str(request.url.path)
        }
    )

def get_scoring_service(db: Session = Depends(get_db)) -> ScoringService:
    """Dependecy Injection function for the scoring service"""
    # Simply returns a scoring service object
    return ScoringService(db)

@app.post("/tournaments", response_model=TournamentResponse, status_code=201)
def create_tournament(
    tournament_data: TournamentCreate,
    db: Session = Depends(get_db)
) -> Tournament:
    """Endpoint to create a new tournament"""
    try:
        # Initializing the tournament object
        tournament = Tournament(
            name = tournament_data.name,
            organizer_id = tournament_data.organizer_id
        )
        
        # Adding the tournament to the database
        db.add(tournament)
        db.commit()
        db.refresh(tournament)
        
        # Returning the tournament object
        return tournament
    
    except Exception as e:
        # Exception Handling Block
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create tournament: {str(e)}")
    
@app.post("/teams", response_model=TeamResponse, status_code=201)
def create_team(
    team_data: TeamCreate,
    db: Session = Depends(get_db)
) -> Team:
    """Endpoint to create a new team"""
    try:
        # Creating the team object
        team = Team(
            name = team_data.name,
            tournament_id = team_data.tournament_id
        )

        # Adding the team to the database
        db.add(team)
        db.commit()
        db.refresh(team)

        # Returning the team object
        return team

    except Exception as e:
        # Exception Handling Block
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create team: {str(e)}")
    
@app.post("/matches", response_model=MatchResponse, status_code=201)
def create_match(
    match_data: MatchCreate,
    service: ScoringService = Depends(get_scoring_service)
) -> Match:
    """Endpoint to create a new match"""
    try:
        # Creating the match using the scoring service
        match = service.create_match(
            tournament_id = match_data.tournament_id,
            team1_id = match_data.team1_id,
            team2_id = match_data.team2_id
        )

        # Checking if match was created successfully
        if match is None:
            raise HTTPException(status_code=404, detail="Failed to create match")
        
        # Returning the match object
        return match
    
    except HTTPException:
        # Re-raising HTTP exceptions
        raise
    
    except Exception as e:
        # Exception Handling Block
        raise HTTPException(status_code=500, detail=f"Failed to create match: {str(e)}")

@app.get("/matches/{match_id}", response_model=MatchResponse, status_code=200)
def get_match(
    match_id: int,
    service: ScoringService = Depends(get_scoring_service)
) -> Match:
    """Endpoint to get a match by ID"""
    try:
        # Retrieving the match using the scoring service
        match = service.get_match(match_id=match_id)

        # Checking if match was found
        if match is None:
            raise HTTPException(status_code=404, detail="Match not found")
        
        # Returning the match object
        return match
    
    except HTTPException:
        # Re-raising HTTP exceptions
        raise
    
    except Exception as e:
        # Exception Handling Block
        raise HTTPException(status_code=500, detail=f"Failed to retrieve match: {str(e)}")

@app.post("/matches/{match_id}/initialize", response_model=MatchResponse, status_code=200)
def initialize_match_score(
    match_id: int,
    init_data: MatchInitialize,
    service: ScoringService = Depends(get_scoring_service)
) -> Match:
    """Endpoint to initialize the score information for a match"""
    try:
        # Initializing the score using the scoring service
        match = service.initialize_score(
            match_id = match_id,
            batting_team_id = init_data.batting_team_id,
            bowling_team_id = init_data.bowling_team_id
        )

        # Checking if initialization was successful
        if match is None:
            raise HTTPException(status_code=404, detail="Match not found")
        
        # Returning the initialized match object
        return match
    
    except HTTPException:
        # Re-raising HTTP exceptions
        raise
    
    except Exception as e:
        # Exception Handling Block
        raise HTTPException(status_code=500, detail=f"Failed to initialize match score: {str(e)}")

@app.post("/matches/{match_id}/ball", response_model=MatchResponse, status_code=200)
def process_ball(
    match_id: int,
    ball_data: BallEvent,
    service: ScoringService = Depends(get_scoring_service)
) -> Match:
    """Endpoint to process a ball event"""
    try:
        # Converting the Pydantic model to a dictionary
        ball_dict = ball_data.model_dump()

        # Processing the ball event using the scoring service
        match = service.process_ball_event(
            match_id = match_id,
            ball_data = ball_dict
        )

        # Checking if processing was successful
        if match is None:
            raise HTTPException(status_code=400, detail="Failed to process ball event")
        
        # Returning the updated match object
        return match
    
    except HTTPException:
        # Re-raising HTTP exceptions
        raise
    
    except Exception as e:
        # Exception Handling Block
        raise HTTPException(status_code=500, detail=f"Failed to process ball event: {str(e)}")

@app.get("/tournaments/{tournament_id}/matches", response_model=List[MatchResponse], status_code=200)
def get_tournament_matches(
    tournament_id: int,
    service: ScoringService = Depends(get_scoring_service)
) -> List[Match]:
    """Endpoint to get all matches for a tournament"""
    try:
        # Retrieving all matches for the tournament using the scoring service
        matches = service.get_matches_by_tournament(tournament_id=tournament_id)

        # Returning the list of matches
        return matches
    
    except Exception as e:
        # Exception Handling Block
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tournament matches: {str(e)}")

@app.post("/matches/{match_id}/complete", response_model=MatchResponse, status_code=200)
def complete_match(
    match_id: int,
    service: ScoringService = Depends(get_scoring_service)
) -> Match:
    """Endpoint to mark a match as completed"""
    try:
        # Marking the match as completed using the scoring service
        match = service.complete_match(match_id=match_id)

        # Checking if the match was found
        if match is None:
            raise HTTPException(status_code=404, detail="Match not found")
        
        # Returning the completed match object
        return match
    
    except HTTPException:
        # Re-raising HTTP exceptions
        raise
    
    except Exception as e:
        # Exception Handling Block
        raise HTTPException(status_code=500, detail=f"Failed to complete match: {str(e)}")

@app.get("/health", status_code=200)
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint to verify API and database connectivity"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        
        # Test Redis connection
        redis_client = get_redis()
        redis_client.ping()
        
        return {
            "status": "healthy",
            "version": "1.0.0",
            "database": "connected",
            "redis": "connected"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)