import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import engine, redis_db, get_db, get_redis
from sqlalchemy import text

print("=== Testing Raw Connections ===")

print("\n1. Testing PostgreSQL engine directly...")
with engine.connect() as conn:
    result = conn.execute(text("SELECT 1 as test"))
    print(f"   Raw engine result: {result.fetchone()}")

print("\n2. Testing Redis client directly...")
redis_db.set('raw_test', 'direct')
print(f"   Raw redis result: {redis_db.get('raw_test')}")

print("\n=== Testing Dependency Functions ===")

print("\n3. Testing get_db() dependency...")
db_gen = get_db()
session = next(db_gen)
try:
    result = session.execute(text("SELECT 2 as test"))
    print(f"   get_db() result: {result.fetchone()}")
finally:
    try:
        next(db_gen)
    except StopIteration:
        pass
 
print("\n4. Testing get_redis() dependency...")
redis_client = get_redis()
redis_client.set('dep_test', 'from_function')
print(f"   get_redis() result: {redis_client.get('dep_test')}")

print("\nAll tests passed!")