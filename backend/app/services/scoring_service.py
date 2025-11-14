from uuid import uuid4
from typing import Dict
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.match import Match, MatchStatus

class ScoringService:

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_match(self, tournament_id: int, team1_id: int, team2_id: int) -> Match:
        """Method for creating a new match object"""
        # Creating a new Match object
        new_match = Match(
            tournament_id = tournament_id,
            team1_id = team1_id,
            team2_id = team2_id,
            status = MatchStatus.SCHEDULED,
            score_data = None,
            created_at = datetime.now(timezone.utc)
        )

        try:
            # Adding the new Match object to the session
            self.session.add(new_match)

            # Commit and refresh
            self.session.commit()
            self.session.refresh(new_match)

            return new_match

        except Exception as e:
            # Exception Handling block
            print(f"Failed to create a new Match object: \n{e}")
            self.session.rollback()
            raise

    def get_match(self, match_id: int) -> Match | None:
        """Method for getting match from the database"""
        try:
            # Query the matches table using the provided ID
            match_by_id = self.session.query(Match).filter_by(id=match_id).first()

            # Checking if a match was retrieved
            if match_by_id:
                return match_by_id
            else:
                return None
        
        except Exception as e:
            # Exception Handling Block
            print(f"Failed to retrieve match due to an error: \n{e}")
            raise
        
    def initialize_score(
        self,
        match_id: int,
        batting_team_id: int,
        bowling_team_id: int
    ) -> Match | None:
        """Method for initializing the score information"""
        try:
            # Retrieving the existing match object
            match_by_id = self.get_match(match_id=match_id)

            if match_by_id:
                # Creating the initial score dictionary
                score_data = {
                    "innings": 1,
                    "batting_team_id": batting_team_id,
                    "bowling_team_id": bowling_team_id,
                    "score": 0,
                    "wickets": 0,
                    "overs": 0.0,
                    "current_batsmen": [],
                    "current_bowler": None,
                    "last_ball": None,
                    "commentary": "Match is about to start..."
                }

                # Adding the new score information and starting the match
                match_by_id.score_data = score_data
                match_by_id.status = MatchStatus.IN_PROGRESS

                # Commiting the session
                self.session.commit()

                return match_by_id

            else:
                # In case the match was not found
                print(f"Match not found for the ID: {match_id}")
                return None
            
        except Exception as e:
            # Exception Handling block
            print(f"Failed to initialize score information due to an error:\n{e}")
            raise

    def update_score(self, match_id: int, updates: Dict) -> Match | None:
        """Method to update the score dictionary in a Match object"""
        try:
            # Checking if the match exists
            match_by_id = self.get_match(match_id=match_id)

            if match_by_id:
                # Checking if the score information exists
                if match_by_id.score_data is None:
                    if match_by_id.score_data is None:
                        print("Error: Score not initialized!")
                        return None

                # Iterating through the dictionary with score updates
                for key, item in updates.items():
                    if key in match_by_id.score_data:
                        match_by_id.score_data[key] = item
                    else:
                        print(f"Warning key: {key} is not in existing score information, skipping!")

                # Commiting the session
                self.session.commit()

                return match_by_id
            
            else:
                # In case the match was not found
                print(f"Match not found for the ID: {match_id}")
                return None
            
        except Exception as e:
            # Exception Handling block
            print(f"Failed to update score information due to an error:\n{e}")
            raise