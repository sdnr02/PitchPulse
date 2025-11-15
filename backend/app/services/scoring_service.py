from uuid import uuid4
from typing import Dict, List
from datetime import datetime, timezone

from sqlalchemy import desc
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

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
                flag_modified(match_by_id, "score_data")
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
                    print("Error: Score not initialized!")
                    return None

                # Iterating through the dictionary with score updates
                for key, item in updates.items():
                    if key in match_by_id.score_data:
                        match_by_id.score_data[key] = item
                    else:
                        print(f"Warning key: {key} is not in existing score information, skipping!")

                # Commiting the session
                flag_modified(match_by_id, "score_data")
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
    
    def _calculate_new_overs(self, current_overs: float, is_legal_ball: bool) -> float:
        """Method to calculate the overs after incrementing"""
        try:
            # Getting the over and balls split
            over = int(current_overs)
            balls = int((current_overs*10)%10)

            if is_legal_ball:
                # Checking if the over is done
                if (balls + 1) == 6:
                    balls = 0
                    over = over + 1
                else:
                    balls = balls + 1

                # Recombining the overs to a floating point
                new_overs = over + (balls/10)
                return new_overs
            
            else:
                return current_overs
            
        except Exception as e:
            print(f"Error in calculating new overs after incrementing:\n{e}")
            return current_overs

    def process_ball_event(self, match_id: int, ball_data: Dict) -> Match | None:
        """Method to update match data ball-by-ball"""
        try:
            # Checking if the match exists
            match_by_id = self.get_match(match_id=match_id)

            # Checking if both the match and the score information exist
            if not match_by_id:
                print(f"Match not found for ID: {match_id}")
                return None
                
            if match_by_id.score_data is None:
                print("Error: Score not initialized!")
                return None

            # Extracting current state
            current_score = match_by_id.score_data["score"]
            current_wickets = match_by_id.score_data["wickets"]
            current_overs = match_by_id.score_data["overs"]

            # Updating score with runs
            new_score = current_score + ball_data["runs"]
            match_by_id.score_data["score"] = new_score

            # Handling if the ball was a wicket
            if ball_data["is_wicket"]:
                match_by_id.score_data["wickets"] = current_wickets + 1
                
                # Removing dismissed batsman from current batsmen list
                dismissed_batsman = ball_data["batsman_name"]
                updated_batsmen = []
                
                for batsman in match_by_id.score_data["current_batsmen"]:
                    if batsman.get("name") != dismissed_batsman:
                        updated_batsmen.append(batsman)
                
                match_by_id.score_data["current_batsmen"] = updated_batsmen

            # Calculating new overs for both legal and illegal balls
            if ball_data["extra_type"] is None:
                new_overs = self._calculate_new_overs(current_overs, is_legal_ball=True)
            else:
                new_overs = self._calculate_new_overs(current_overs, is_legal_ball=False)
            
            match_by_id.score_data["overs"] = new_overs

            # Updating current batsmen information
            batsman_found = False
            for batsman in match_by_id.score_data["current_batsmen"]:
                if batsman["name"] == ball_data["batsman_name"]:
                    batsman["runs"] = batsman["runs"] + ball_data["runs"]
                    if ball_data["extra_type"] is None:
                        batsman["balls"] = batsman["balls"] + 1
                    batsman_found = True
                    break
            
            # Adding new batsman if not found
            if not batsman_found:
                # If first ball was an extra
                if ball_data["extra_type"] is None:
                    balls = 1
                else:
                    balls = 0

                # Adding score information with that batsman
                match_by_id.score_data["current_batsmen"].append({
                    "name": ball_data["batsman_name"],
                    "runs": ball_data["runs"],
                    "balls": balls
                })

            # Updating current bowler information
            if match_by_id.score_data["current_bowler"] is None:
                # Checking if the ball was legal
                if ball_data["extra_type"] is None:
                    bowler_overs = new_overs
                else:
                    bowler_overs = 0.0

                # Checking if the ball was a wicket
                if ball_data["is_wicket"]:
                    bowler_wickets = 1
                else:
                    bowler_wickets = 0

                # Creating new bowler entry
                match_by_id.score_data["current_bowler"] = {
                    "name": ball_data["bowler_name"],
                    "overs": bowler_overs,
                    "runs": ball_data["runs"],
                    "wickets": bowler_wickets
                }
            
            else:
                # Updating existing bowler
                bowler = match_by_id.score_data["current_bowler"]
                
                # Checking if the same bowler is continuing
                if bowler["name"] == ball_data["bowler_name"]:
                    # Updating overs if legal ball
                    if ball_data["extra_type"] is None:
                        bowler["overs"] = new_overs
                    
                    # Updating runs and wickets
                    bowler["runs"] = bowler["runs"] + ball_data["runs"]
                    if ball_data["is_wicket"]:
                        bowler["wickets"] = bowler["wickets"] + 1

                else:
                    # Checking if the ball was legal
                    if ball_data["extra_type"] is None:
                        bowler_overs = new_overs
                    else:
                        bowler_overs = 0.0

                    # Checking if the ball was a wicket
                    if ball_data["is_wicket"]:
                        bowler_wickets = 1
                    else:
                        bowler_wickets = 0

                    # New bowler taking over
                    match_by_id.score_data["current_bowler"] = {
                        "name": ball_data["bowler_name"],
                        "overs": bowler_overs,
                        "runs": ball_data["runs"],
                        "wickets": bowler_wickets
                    }

            # Storing last ball information
            match_by_id.score_data["last_ball"] = {
                "runs": ball_data["runs"],
                "is_wicket": ball_data["is_wicket"],
                "extra_type": ball_data["extra_type"]
            }

            # Updating commentary
            match_by_id.score_data["commentary"] = ball_data["commentary"]

            # Commiting the session
            flag_modified(match_by_id, "score_data")
            self.session.commit()

            return match_by_id
        
        except Exception as e:
            # Exception Handling block
            print(f"Failed to process ball event due to an error:\n{e}")
            self.session.rollback()
            raise

    def get_matches_by_tournament(self, tournament_id: int) -> List[Match]:
        """Method to get all the matches from a tournament"""
        try:
            # Querying the list of matches in a tournament
            matches = self.session.query(Match).filter_by(tournament_id=tournament_id).order_by(desc(Match.created_at)).all()
            return matches

        except Exception as e:
            # Exception Handling block
            print(f"Failed to retrieve matches by tournament due to an error:\n{e}")
            raise

    def complete_match(self, match_id: int) -> Match | None:
        """Method to mark a match as completed"""
        try:
            # Getting the match
            match_by_id = self.get_match(match_id=match_id)
            
            if match_by_id:
                # Setting the status to completed
                match_by_id.status = MatchStatus.COMPLETED
                
                # Commiting the session
                self.session.commit()
                return match_by_id
            
            else:
                # In case the match was not found
                print(f"Match not found for the ID: {match_id}")
                return None
        
        except Exception as e:
            # Exception Handling block
            print(f"Failed to complete match due to an error:\n{e}")
            self.session.rollback()
            raise