from enum import Enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base

class MatchStatus(Enum):
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"

class User(Base):
    """Models class for the Users table"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(TIMESTAMP)

    tournaments = relationship("Tournament", back_populates="organizer")

    def __repr__(self):
        return f"User ID: {self.id}, Email ID: {self.email}"

class Tournament(Base):
    """Models class used for the Tournaments table"""
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP)

    organizer = relationship("User", back_populates="tournaments")
    teams = relationship("Team", back_populates="tournament")
    matches = relationship("Match", back_populates="match_tournament")

    def __repr__(self):
        return f"Tournament Name: {self.name}, Organizer ID: {self.organizer_id}"
    
class Team(Base):
    """Models class used for the Teams table"""
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)

    tournament = relationship("Tournament", back_populates="teams")
    team1_matches = relationship("Match", foreign_keys="[Match.team1_id]", back_populates="team1")
    team2_matches = relationship("Match", foreign_keys="[Match.team2_id]", back_populates="team2")

    def __repr__(self):
        return f"Team ID: {self.id}, Team Name: {self.name}"
    
class Match(Base):
    """Models class used for the Matches table"""
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    team1_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    team2_id = Column(Integer, ForeignKey("teams.id"), nullable=False)

    status = Column(SQLEnum(MatchStatus, name="match_status_enum"), default=MatchStatus.SCHEDULED)

    # We make this nullable since a new match will not have score data
    score_data = Column(JSONB, nullable=True)

    created_at = Column(TIMESTAMP)

    # Need to point sqlalchemy to which foreign key that relationship uses
    team1 = relationship("Team", foreign_keys=[team1_id], back_populates="team1_matches")
    team2 = relationship("Team", foreign_keys=[team2_id], back_populates="team2_matches")
    match_tournament = relationship("Tournament", back_populates="matches")

    def __repr__(self):
        return f"Match: {self.id}, Tournament: {self.tournament_id}, {self.team1_id} vs {self.team2_id}"