# Warning: This file was AI generated

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.models.match import User, Tournament, Team, Match, MatchStatus
from sqlalchemy.inspection import inspect

print("=== Testing Model Imports ===")
print("All models imported successfully!\n")

# Test 1: Check table names
print("=== Testing Table Names ===")
print(f"User table: {User.__tablename__}")
print(f"Tournament table: {Tournament.__tablename__}")
print(f"Team table: {Team.__tablename__}")
print(f"Match table: {Match.__tablename__}")
print()

# Test 2: Check columns exist
print("=== Testing Columns ===")

def print_columns(model):
    mapper = inspect(model)
    print(f"\n{model.__name__} columns:")
    for column in mapper.columns:
        print(f"  - {column.name}: {column.type}")

print_columns(User)
print_columns(Tournament)
print_columns(Team)
print_columns(Match)
print()

# Test 3: Check relationships
print("=== Testing Relationships ===")

def print_relationships(model):
    mapper = inspect(model)
    print(f"\n{model.__name__} relationships:")
    for rel in mapper.relationships:
        print(f"  - {rel.key} → {rel.mapper.class_.__name__}")

print_relationships(User)
print_relationships(Tournament)
print_relationships(Team)
print_relationships(Match)
print()

# Test 4: Check foreign keys
print("=== Testing Foreign Keys ===")

def print_foreign_keys(model):
    mapper = inspect(model)
    fks = []
    for column in mapper.columns:
        if column.foreign_keys:
            for fk in column.foreign_keys:
                fks.append(f"  - {column.name} → {fk.target_fullname}")
    if fks:
        print(f"\n{model.__name__} foreign keys:")
        for fk in fks:
            print(fk)
    else:
        print(f"\n{model.__name__}: No foreign keys")

print_foreign_keys(User)
print_foreign_keys(Tournament)
print_foreign_keys(Team)
print_foreign_keys(Match)
print()

# Test 5: Test Enum values
print("=== Testing Match Status Enum ===")
print("Available statuses:")
for status in MatchStatus:
    print(f"  - {status.name}: {status.value}")
print()

# Test 6: Test __repr__ methods (create instances without saving)
print("=== Testing __repr__ Methods ===")

# Create instances (not saved to DB)
user = User(id=1, email="test@example.com", password_hash="hashed_password")
print(f"User: {user}")

tournament = Tournament(id=1, name="Test Tournament", organizer_id=1)
print(f"Tournament: {tournament}")

team = Team(id=1, name="Test Team", tournament_id=1)
print(f"Team: {team}")

match = Match(
    id=1, 
    tournament_id=1, 
    team1_id=1, 
    team2_id=2,
    status=MatchStatus.SCHEDULED
)
print(f"Match: {match}")
print()

# Test 7: Verify back_populates connections
print("=== Verifying back_populates Connections ===")

def verify_backpopulates(model, rel_name, expected_target, expected_back):
    mapper = inspect(model)
    rel = mapper.relationships.get(rel_name)
    if rel:
        target_class = rel.mapper.class_.__name__
        back_populates = rel.back_populates
        status = "[OK]" if target_class == expected_target and back_populates == expected_back else "[FAIL]"
        print(f"{status} {model.__name__}.{rel_name} → {target_class} (back_populates: {back_populates})")
        return target_class == expected_target and back_populates == expected_back
    else:
        print(f"{model.__name__}.{rel_name} not found!")
        return False

all_good = True

# User ↔ Tournament
all_good &= verify_backpopulates(User, "tournaments", "Tournament", "organizer")
all_good &= verify_backpopulates(Tournament, "organizer", "User", "tournaments")

# Tournament ↔ Team
all_good &= verify_backpopulates(Tournament, "teams", "Team", "tournament")
all_good &= verify_backpopulates(Team, "tournament", "Tournament", "teams")

# Tournament ↔ Match
all_good &= verify_backpopulates(Tournament, "matches", "Match", "match_tournament")
all_good &= verify_backpopulates(Match, "match_tournament", "Tournament", "matches")

# Team ↔ Match (two relationships)
all_good &= verify_backpopulates(Team, "team1_matches", "Match", "team1")
all_good &= verify_backpopulates(Match, "team1", "Team", "team1_matches")
all_good &= verify_backpopulates(Team, "team2_matches", "Match", "team2")
all_good &= verify_backpopulates(Match, "team2", "Team", "team2_matches")

print()

# Test 8: Check JSONB column
print("=== Testing JSONB Column ===")
match_mapper = inspect(Match)
score_data_col = match_mapper.columns.get('score_data')
if score_data_col is not None:
    print(f"   score_data column exists")
    print(f"   Type: {score_data_col.type}")
    print(f"   Nullable: {score_data_col.nullable}")
else:
    print("   score_data column not found!")
    all_good = False

print()

# Test 9: Test score_data structure (without DB)
print("=== Testing score_data Structure ===")
sample_score = {
    "innings": 1,
    "batting_team_id": 1,
    "bowling_team_id": 2,
    "score": 154,
    "wickets": 3,
    "overs": 18.4,
    "current_batsmen": [
        {"player_id": 1, "name": "Rohit", "runs": 78, "balls": 50}
    ],
    "current_bowler": {"player_id": 21, "name": "Starc", "overs": 3.4},
    "last_ball": {"runs": 4, "is_wicket": False},
    "commentary": "Four!"
}

match_with_score = Match(
    id=1,
    tournament_id=1,
    team1_id=1,
    team2_id=2,
    score_data=sample_score
)

print(f"   score_data can be set as dict")
print(f"   Sample score: {match_with_score.score_data['score']}")
print(f"   Sample wickets: {match_with_score.score_data['wickets']}")
print()

# Final result
print("=" * 50)
if all_good:
    print(" ALL TESTS PASSED! Models class is Ready!")
else:
    print("  Some tests failed. Review the errors above.")
print("=" * 50)