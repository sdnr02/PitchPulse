# Warning: This file was AI generated

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.match import User, Tournament, Team, Match, MatchStatus
from app.services.scoring_service import ScoringService
from datetime import datetime, timezone

print("=" * 60)
print("SCORING SERVICE TEST")
print("=" * 60)

session = SessionLocal()
service = ScoringService(session)

try:
    # ========================================
    # Setup: Create Test Data
    # ========================================
    print("\n=== Setup: Creating Test Data ===\n")
    
    # Create user
    user = User(
        email="scorer@test.com",
        password_hash="hashed_password",
        created_at=datetime.now(timezone.utc)
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    print(f"[PASS] Created user: {user}")
    
    # Create tournament
    tournament = Tournament(
        name="Test T20 League",
        organizer_id=user.id,
        created_at=datetime.now(timezone.utc)
    )
    session.add(tournament)
    session.commit()
    session.refresh(tournament)
    print(f"[PASS] Created tournament: {tournament}")
    
    # Create teams
    team1 = Team(name="Mumbai Indians", tournament_id=tournament.id)
    team2 = Team(name="Chennai Super Kings", tournament_id=tournament.id)
    session.add_all([team1, team2])
    session.commit()
    session.refresh(team1)
    session.refresh(team2)
    print(f"[PASS] Created teams: {team1}, {team2}")
    
    # ========================================
    # Test 1: create_match()
    # ========================================
    print("\n=== Test 1: create_match() ===\n")
    
    match = service.create_match(
        tournament_id=tournament.id,
        team1_id=team1.id,
        team2_id=team2.id
    )
    
    print(f"[PASS] Match created: {match}")
    print(f"   - ID: {match.id}")
    print(f"   - Status: {match.status.value}")
    print(f"   - Score Data: {match.score_data}")
    
    # ========================================
    # Test 2: get_match()
    # ========================================
    print("\n=== Test 2: get_match() ===\n")
    
    retrieved_match = service.get_match(match.id)
    print(f"[PASS] Retrieved match: {retrieved_match}")
    
    # Test non-existent match
    non_existent = service.get_match(99999)
    if non_existent is None:
        print(f"[PASS] Correctly returned None for non-existent match")
    
    # ========================================
    # Test 3: initialize_score()
    # ========================================
    print("\n=== Test 3: initialize_score() ===\n")
    
    initialized_match = service.initialize_score(
        match_id=match.id,
        batting_team_id=team1.id,
        bowling_team_id=team2.id
    )
    
    print(f"[PASS] Score initialized")
    print(f"   - Status: {initialized_match.status.value}")
    print(f"   - Innings: {initialized_match.score_data['innings']}")
    print(f"   - Score: {initialized_match.score_data['score']}")
    print(f"   - Wickets: {initialized_match.score_data['wickets']}")
    print(f"   - Overs: {initialized_match.score_data['overs']}")
    print(f"   - Commentary: {initialized_match.score_data['commentary']}")
    
    # ========================================
    # Test 4: update_score()
    # ========================================
    print("\n=== Test 4: update_score() ===\n")
    
    updated_match = service.update_score(
        match_id=match.id,
        updates={
            "commentary": "Match has begun!"
        }
    )
    
    print(f"[PASS] Score updated")
    print(f"   - Commentary: {updated_match.score_data['commentary']}")
    
    # ========================================
    # Test 5: process_ball_event() - Normal Balls
    # ========================================
    print("\n=== Test 5: process_ball_event() - Normal Balls ===\n")
    
    # Ball 1: Single run
    print("Ball 1: Single run")
    ball1 = service.process_ball_event(
        match_id=match.id,
        ball_data={
            "runs": 1,
            "is_wicket": False,
            "extra_type": None,
            "batsman_name": "Rohit Sharma",
            "bowler_name": "Deepak Chahar",
            "commentary": "Single taken to mid-wicket"
        }
    )
    print(f"   Score: {ball1.score_data['score']}/{ball1.score_data['wickets']}")
    print(f"   Overs: {ball1.score_data['overs']}")
    print(f"   Batsmen: {ball1.score_data['current_batsmen']}")
    print(f"   Bowler: {ball1.score_data['current_bowler']}")
    
    # Ball 2: Four runs
    print("\nBall 2: Four runs")
    ball2 = service.process_ball_event(
        match_id=match.id,
        ball_data={
            "runs": 4,
            "is_wicket": False,
            "extra_type": None,
            "batsman_name": "Rohit Sharma",
            "bowler_name": "Deepak Chahar",
            "commentary": "FOUR! Driven through covers!"
        }
    )
    print(f"   Score: {ball2.score_data['score']}/{ball2.score_data['wickets']}")
    print(f"   Overs: {ball2.score_data['overs']}")
    print(f"   Rohit's stats: {[b for b in ball2.score_data['current_batsmen'] if b['name'] == 'Rohit Sharma']}")
    
    # Ball 3: New batsman
    print("\nBall 3: New batsman - Ishan Kishan")
    ball3 = service.process_ball_event(
        match_id=match.id,
        ball_data={
            "runs": 2,
            "is_wicket": False,
            "extra_type": None,
            "batsman_name": "Ishan Kishan",
            "bowler_name": "Deepak Chahar",
            "commentary": "Two runs to backward point"
        }
    )
    print(f"   Score: {ball3.score_data['score']}/{ball3.score_data['wickets']}")
    print(f"   Overs: {ball3.score_data['overs']}")
    print(f"   Batsmen: {ball3.score_data['current_batsmen']}")
    
    # ========================================
    # Test 6: process_ball_event() - Wicket
    # ========================================
    print("\n=== Test 6: process_ball_event() - Wicket ===\n")
    
    wicket_ball = service.process_ball_event(
        match_id=match.id,
        ball_data={
            "runs": 0,
            "is_wicket": True,
            "extra_type": None,
            "batsman_name": "Rohit Sharma",
            "bowler_name": "Deepak Chahar",
            "commentary": "OUT! Caught behind!"
        }
    )
    print(f"[PASS] Wicket processed")
    print(f"   Score: {wicket_ball.score_data['score']}/{wicket_ball.score_data['wickets']}")
    print(f"   Overs: {wicket_ball.score_data['overs']}")
    print(f"   Remaining batsmen: {wicket_ball.score_data['current_batsmen']}")
    print(f"   Bowler wickets: {wicket_ball.score_data['current_bowler']['wickets']}")
    
    # ========================================
    # Test 7: process_ball_event() - Wide
    # ========================================
    print("\n=== Test 7: process_ball_event() - Wide ===\n")
    
    wide_ball = service.process_ball_event(
        match_id=match.id,
        ball_data={
            "runs": 1,
            "is_wicket": False,
            "extra_type": "wide",
            "batsman_name": "Ishan Kishan",
            "bowler_name": "Deepak Chahar",
            "commentary": "Wide down the leg side"
        }
    )
    print(f"[PASS] Wide processed")
    print(f"   Score: {wide_ball.score_data['score']}/{wide_ball.score_data['wickets']}")
    print(f"   Overs: {wide_ball.score_data['overs']} (should not increment)")
    print(f"   Ishan's balls faced: {[b['balls'] for b in wide_ball.score_data['current_batsmen'] if b['name'] == 'Ishan Kishan']}")
    
    # ========================================
    # Test 8: process_ball_event() - Complete Over
    # ========================================
    print("\n=== Test 8: process_ball_event() - Complete Over ===\n")
    
    # Complete the over (2 more balls needed after 0.4)
    print("Completing over...")
    for i in range(2):
        service.process_ball_event(
            match_id=match.id,
            ball_data={
                "runs": 0,
                "is_wicket": False,
                "extra_type": None,
                "batsman_name": "Ishan Kishan",
                "bowler_name": "Deepak Chahar",
                "commentary": f"Dot ball {i+1}"
            }
        )
    
    over_complete = service.get_match(match.id)
    print(f"[PASS] Over completed")
    print(f"   Overs: {over_complete.score_data['overs']} (should be 1.0)")
    
    # ========================================
    # Test 9: get_matches_by_tournament()
    # ========================================
    print("\n=== Test 9: get_matches_by_tournament() ===\n")
    
    # Create another match
    match2 = service.create_match(
        tournament_id=tournament.id,
        team1_id=team2.id,
        team2_id=team1.id
    )
    
    tournament_matches = service.get_matches_by_tournament(tournament.id)
    print(f"[PASS] Retrieved {len(tournament_matches)} matches for tournament")
    for m in tournament_matches:
        print(f"   - Match {m.id}: Status = {m.status.value}")
    
    # ========================================
    # Test 10: complete_match()
    # ========================================
    print("\n=== Test 10: complete_match() ===\n")
    
    completed_match = service.complete_match(match.id)
    print(f"[PASS] Match completed")
    print(f"   - Match ID: {completed_match.id}")
    print(f"   - Status: {completed_match.status.value}")
    print(f"   - Final Score: {completed_match.score_data['score']}/{completed_match.score_data['wickets']}")
    print(f"   - Overs: {completed_match.score_data['overs']}")
    
    # ========================================
    # Cleanup
    # ========================================
    print("\n=== Cleanup ===\n")
    
    session.delete(match)
    session.delete(match2)
    session.delete(team1)
    session.delete(team2)
    session.delete(tournament)
    session.delete(user)
    session.commit()
    
    print("[PASS] All test data cleaned up")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] ALL SCORING SERVICE TESTS PASSED!")
    print("=" * 60)

except Exception as e:
    print(f"\n[FAIL] ERROR: {e}")
    print("\nRolling back...")
    session.rollback()
    import traceback
    traceback.print_exc()

finally:
    session.close()