import sys
from pathlib import Path

# Ensure app is importable
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import engine, SessionLocal
from app.models.match import User, Tournament, Team, Match, MatchStatus
from sqlalchemy import text
from datetime import datetime

print("=" * 60)
print("ALEMBIC MIGRATION VERIFICATION TEST")
print("=" * 60)

# ========================================
# Part 1: Verify Tables Were Created
# ========================================
print("\n=== Part 1: Checking Tables in Database ===\n")

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """))
    
    tables = result.fetchall()
    
    if tables:
        print("[PASS] Tables created:")
        for table in tables:
            print(f"   - {table[0]}")
    else:
        print("[FAIL] No tables found!")
        exit(1)

# Check specific table structure
print("\n=== Checking 'matches' Table Structure ===")
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'matches'
        ORDER BY ordinal_position
    """))
    
    columns = result.fetchall()
    if columns:
        print("[PASS] Columns in matches table:")
        for col in columns:
            print(f"   - {col[0]}: {col[1]}")
    else:
        print("[FAIL] Matches table not found!")
        exit(1)

# ========================================
# Part 2: Test Basic CRUD Operations
# ========================================
print("\n=== Part 2: Testing CRUD Operations ===\n")

session = SessionLocal()

try:
    # Create a user
    print("1. Creating user...")
    user = User(
        email="test@pitchpulse.com",
        password_hash="hashed_password_here",
        created_at=datetime.utcnow()
    )
    session.add(user)
    session.commit()
    session.refresh(user)  # Get the ID assigned by database
    print(f"   [PASS] {user}")
    
    # Create a tournament
    print("\n2. Creating tournament...")
    tournament = Tournament(
        name="Test IPL 2025",
        organizer_id=user.id,
        created_at=datetime.utcnow()
    )
    session.add(tournament)
    session.commit()
    session.refresh(tournament)
    print(f"   [PASS] {tournament}")
    
    # Create teams
    print("\n3. Creating teams...")
    team1 = Team(name="CSK", tournament_id=tournament.id)
    team2 = Team(name="MI", tournament_id=tournament.id)
    session.add_all([team1, team2])
    session.commit()
    session.refresh(team1)
    session.refresh(team2)
    print(f"   [PASS] {team1}")
    print(f"   [PASS] {team2}")
    
    # Create a match with score data
    print("\n4. Creating match with JSONB score_data...")
    match = Match(
        tournament_id=tournament.id,
        team1_id=team1.id,
        team2_id=team2.id,
        status=MatchStatus.SCHEDULED,
        score_data={
            "innings": 1,
            "batting_team_id": team1.id,
            "bowling_team_id": team2.id,
            "score": 0,
            "wickets": 0,
            "overs": 0.0,
            "commentary": "Match about to start..."
        },
        created_at=datetime.utcnow()
    )
    session.add(match)
    session.commit()
    session.refresh(match)
    print(f"   [PASS] {match}")
    print(f"   [PASS] Score data stored: {match.score_data}")
    
    # ========================================
    # Part 3: Test Relationships
    # ========================================
    print("\n=== Part 3: Testing Relationships ===\n")
    
    # Test User → Tournaments
    print("1. User → Tournaments relationship:")
    user = session.query(User).first()
    print(f"   User {user.email} has {len(user.tournaments)} tournament(s)")
    for t in user.tournaments:
        print(f"     - {t.name}")
    
    # Test Tournament → Teams
    print("\n2. Tournament → Teams relationship:")
    tournament = session.query(Tournament).first()
    print(f"   Tournament '{tournament.name}' has {len(tournament.teams)} team(s)")
    for t in tournament.teams:
        print(f"     - {t.name}")
    
    # Test Tournament → Matches
    print("\n3. Tournament → Matches relationship:")
    print(f"   Tournament '{tournament.name}' has {len(tournament.matches)} match(es)")
    for m in tournament.matches:
        print(f"     - Match {m.id}: Team {m.team1_id} vs Team {m.team2_id}")
    
    # Test Match → Teams (both directions)
    print("\n4. Match → Team relationships:")
    match = session.query(Match).first()
    print(f"   Match {match.id}:")
    print(f"     - Team 1: {match.team1.name}")
    print(f"     - Team 2: {match.team2.name}")
    
    # Test Team → Matches (both team1 and team2)
    print("\n5. Team → Matches relationships:")
    team = session.query(Team).filter_by(name="CSK").first()
    print(f"   Team '{team.name}':")
    print(f"     - Matches as team1: {len(team.team1_matches)}")
    print(f"     - Matches as team2: {len(team.team2_matches)}")
    
    # ========================================
    # Part 4: Test JSONB Operations
    # ========================================
    print("\n=== Part 4: Testing JSONB Score Update ===\n")
    
    # Update score
    print("1. Updating score_data...")
    match.score_data["score"] = 45
    match.score_data["wickets"] = 2
    match.score_data["overs"] = 8.3
    match.score_data["commentary"] = "Wicket! Great bowling!"
    session.commit()
    
    # Fetch it back
    match_check = session.query(Match).get(match.id)
    print(f"   [PASS] Updated score: {match_check.score_data['score']}/{match_check.score_data['wickets']}")
    print(f"   [PASS] Commentary: {match_check.score_data['commentary']}")
    
    # ========================================
    # Part 5: Cleanup
    # ========================================
    print("\n=== Part 5: Cleaning Up Test Data ===\n")
    
    session.delete(match)
    session.delete(team1)
    session.delete(team2)
    session.delete(tournament)
    session.delete(user)
    session.commit()
    
    print("   [PASS] All test data cleaned up")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED! DATABASE IS FULLY FUNCTIONAL!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[FAIL] ERROR: {e}")
    print("\nRolling back changes...")
    session.rollback()
    exit(1)
    
finally:
    session.close()