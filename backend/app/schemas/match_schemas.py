from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field

class TournamentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Name of the Tournament")
    organizer_id: int = Field(..., gt=0, description="ID of the Tournament Organizer")

class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Name of the Team")
    tournament_id: int = Field(..., gt=0, description="ID of the Tournament")

class MatchCreate(BaseModel):
    tournament_id: int = Field(..., gt=0, description="ID of the Tournament")
    team1_id: int = Field(..., gt=0, description="ID of the first Team")
    team2_id: int = Field(..., gt=0, description="ID of the second Team")

class MatchInitialize(BaseModel):
    batting_team_id: int = Field(..., gt=0, description="ID of the batting team")
    bowling_team_id: int = Field(..., gt=0, description="ID of the bowling team")

class BallEvent(BaseModel):
    runs: int = Field(..., ge=0, le=10, description="Runs scored (0-10)")
    is_wicket: bool = Field(..., description="Whether a wicket was taken in this ball")
    extra_type: Optional[str] = Field(None, pattern="^(wide|no_ball|bye|leg_bye)$", description="What type of extra the ball was")
    batsman_name: str = Field(..., min_length=1, max_length=100, description="Name of the Batsman at the crease")
    bowler_name: str = Field(..., min_length=1, max_length=100, description="Name of the bowler")
    commentary: str = Field(..., min_length=1, max_length=500, description="Last line of commentary")

class MatchResponse(BaseModel):
    id: int = Field(..., gt=0, description="Unique ID of the Match")
    tournament_id: int = Field(..., gt=0, description="ID of the Tournament")
    team1_id: int = Field(..., gt=0, description="ID of the first Team")
    team2_id: int = Field(..., gt=0, description="ID of the second Team")
    status: str = Field(..., description="Current status of the match (Scheduled, In Progress, Completed)")
    score_data: Optional[Dict] = Field(None, description="JSONB data containing live score information")

    class Config:
        from_attributes = True  # Allows creating from ORM models

class TournamentResponse(BaseModel):
    id: int = Field(..., gt=0, description="Unique ID of the Tournament")
    name: str = Field(..., min_length=1, max_length=255, description="Name of the Tournament")
    organizer_id: int = Field(..., gt=0, description="ID of the Tournament Organizer")
    
    class Config:
        from_attributes = True  # Allows creating from ORM models

class TeamResponse(BaseModel):
    id: int = Field(..., gt=0, description="Unique ID of the Team")
    name: str = Field(..., min_length=1, max_length=255, description="Name of the Team")
    tournament_id: int = Field(..., gt=0, description="ID of the Tournament this team belongs to")
    
    class Config:
        from_attributes = True  # Allows creating from ORM models

class UserCreate(BaseModel):
    email: str = Field(..., min_length=3, max_length=255, description="User email address")
    password_hash: str = Field(..., min_length=1, description="Hashed password")

class UserResponse(BaseModel):
    id: int = Field(..., gt=0, description="Unique ID of the User")
    email: str = Field(..., min_length=3, max_length=255, description="User email address")
    created_at: datetime = Field(..., description="When the user was created")
    
    class Config:
        from_attributes = True