"""
Unit tests for DatabaseManager and RedisManager classes.

This script tests all methods in both managers to ensure they work correctly.
Can be run with pytest or as a standalone script.

Usage:
    pytest scripts/test_managers.py -v
    python scripts/test_managers.py
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

# Import your managers
from core.database import db_manager, redis_manager, DatabaseManager, RedisManager, Base


# Test model for database operations
class TestUser(Base):
    __tablename__ = "test_users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)


class TestDatabaseManager:
    """Test suite for DatabaseManager class"""
    
    @classmethod
    def setup_class(cls):
        """Setup test database before running tests"""
        print("\n" + "="*60)
        print("Setting up DatabaseManager tests...")
        print("="*60)
        db_manager.create_all_tables()
    
    @classmethod
    def teardown_class(cls):
        """Cleanup test database after all tests"""
        print("\n" + "="*60)
        print("Cleaning up DatabaseManager tests...")
        print("="*60)
        
        # Delete all test data before dropping tables
        with db_manager.get_transaction_session() as session:
            session.query(TestUser).delete()
            session.commit()
        
        db_manager.drop_all_tables()
    
    def teardown_method(self, method):
        """Cleanup after each test method"""
        # Ensure all test users are deleted after each test
        with db_manager.get_transaction_session() as session:
            session.query(TestUser).delete()
            session.commit()
    
    def test_health_check(self):
        """Test database health check"""
        print("\n[TEST] Database health check...")
        result = db_manager.health_check()
        assert result is True, "Database health check failed"
        print("[PASS] Database is healthy")
    
    def test_create_tables(self):
        """Test table creation"""
        print("\n[TEST] Creating tables...")
        # Tables should already be created in setup_class
        # This just verifies no errors occur
        db_manager.create_all_tables()
        print("[PASS] Tables created successfully")
    
    def test_get_session_basic(self):
        """Test basic session usage with get_session generator"""
        print("\n[TEST] Basic session usage...")
        session_gen = db_manager.get_session()
        db = next(session_gen)
        
        try:
            # Add a test user
            user = TestUser(name="Alice", email="alice@test.com")
            db.add(user)
            db.commit()
            
            # Query the user
            queried_user = db.query(TestUser).filter_by(email="alice@test.com").first()
            
            # Verify user exists and check attributes
            if queried_user is None:
                raise AssertionError("User not found")
            
            # Type assertion to help Pylance understand this is a string comparison
            user_name: str = queried_user.name  # type: ignore[assignment]
            if user_name != "Alice":
                raise AssertionError("User name mismatch")
            
            # Cleanup
            db.delete(queried_user)
            db.commit()
            
            print("[PASS] Basic session operations work")
        finally:
            # Ensure cleanup even if test fails
            try:
                db.query(TestUser).filter_by(email="alice@test.com").delete()
                db.commit()
            except:
                pass
    
    def test_get_session_with_send(self):
        """Test session usage with send commands"""
        print("\n[TEST] Session with send commands...")
        session_gen = db_manager.get_session()
        db = next(session_gen)
        
        try:
            # Add a test user
            user = TestUser(name="Bob", email="bob@test.com")
            db.add(user)
            
            # Commit using send
            try:
                session_gen.send("commit")
            except StopIteration:
                pass  # Generator exhausted after send
            
            # Verify in a new session
            session_gen2 = db_manager.get_session()
            db2 = next(session_gen2)
            queried_user = db2.query(TestUser).filter_by(email="bob@test.com").first()
            assert queried_user is not None, "User not found after send commit"
            
            # Cleanup
            db2.delete(queried_user)
            db2.commit()
            
            print("[PASS] Send commands work correctly")
        finally:
            # Ensure cleanup
            with db_manager.get_transaction_session() as cleanup_session:
                cleanup_session.query(TestUser).filter_by(email="bob@test.com").delete()
                cleanup_session.commit()
    
    def test_get_transaction_session(self):
        """Test context manager session"""
        print("\n[TEST] Transaction session context manager...")
        
        try:
            # Test successful transaction
            with db_manager.get_transaction_session() as session:
                user = TestUser(name="Charlie", email="charlie@test.com")
                session.add(user)
                session.commit()
            
            # Verify user was saved
            with db_manager.get_transaction_session() as session:
                queried_user = session.query(TestUser).filter_by(email="charlie@test.com").first()
                assert queried_user is not None, "User not found"
                
                # Cleanup
                session.delete(queried_user)
                session.commit()
            
            print("[PASS] Transaction session works")
        finally:
            # Ensure cleanup
            with db_manager.get_transaction_session() as cleanup_session:
                cleanup_session.query(TestUser).filter_by(email="charlie@test.com").delete()
                cleanup_session.commit()
    
    def test_transaction_rollback(self):
        """Test automatic rollback on error"""
        print("\n[TEST] Automatic rollback on error...")
        
        try:
            with db_manager.get_transaction_session() as session:
                user = TestUser(name="Dave", email="dave@test.com")
                session.add(user)
                session.flush()
                raise ValueError("Intentional error for testing")
        except ValueError:
            pass  # Expected error
        
        # Verify user was NOT saved due to rollback
        with db_manager.get_transaction_session() as session:
            queried_user = session.query(TestUser).filter_by(email="dave@test.com").first()
            assert queried_user is None, "User should not exist after rollback"
        
        print("[PASS] Automatic rollback works")
    
    def test_execute_raw_sql(self):
        """Test raw SQL execution"""
        print("\n[TEST] Raw SQL execution...")
        
        try:
            # Insert test data first
            with db_manager.get_transaction_session() as session:
                user = TestUser(name="Eve", email="eve@test.com")
                session.add(user)
                session.commit()
            
            # Execute raw SQL
            query = "SELECT * FROM test_users WHERE email = :email"
            params = {"email": "eve@test.com"}
            results = db_manager.execute_raw_sql(query, params)
            
            assert len(results) == 1, "Expected 1 result"
            assert results[0].name == "Eve", "Name mismatch"
            
            # Cleanup
            with db_manager.get_transaction_session() as session:
                session.query(TestUser).filter_by(email="eve@test.com").delete()
                session.commit()
            
            print("[PASS] Raw SQL execution works")
        finally:
            # Ensure cleanup
            with db_manager.get_transaction_session() as cleanup_session:
                cleanup_session.query(TestUser).filter_by(email="eve@test.com").delete()
                cleanup_session.commit()


class TestRedisManager:
    """Test suite for RedisManager class"""
    
    @classmethod
    def setup_class(cls):
        """Setup before running tests"""
        print("\n" + "="*60)
        print("Setting up RedisManager tests...")
        print("="*60)
        # Clear any test keys that might exist
        test_keys = ["test:user:1", "test:list", "test:dict", "test:expire", "test:delete"]
        for key in test_keys:
            redis_manager.delete(key)
    
    @classmethod
    def teardown_class(cls):
        """Cleanup after all tests"""
        print("\n" + "="*60)
        print("Cleaning up RedisManager tests...")
        print("="*60)
        # Clear test keys
        test_keys = ["test:user:1", "test:list", "test:dict", "test:expire", "test:delete"]
        for key in test_keys:
            redis_manager.delete(key)
    
    def teardown_method(self, method):
        """Cleanup after each test method"""
        # Delete all test keys after each test
        test_keys = ["test:user:1", "test:list", "test:dict", "test:expire", "test:delete"]
        for key in test_keys:
            redis_manager.delete(key)
    
    def test_health_check(self):
        """Test Redis health check"""
        print("\n[TEST] Redis health check...")
        result = redis_manager.health_check()
        assert result is True, "Redis health check failed"
        print("[PASS] Redis is healthy")
    
    def test_set_and_get_json_dict(self):
        """Test storing and retrieving dictionary"""
        print("\n[TEST] Set and get dictionary...")
        
        test_data = {
            "name": "Alice",
            "age": 30,
            "email": "alice@example.com"
        }
        
        try:
            # Store data
            success = redis_manager.set_json("test:user:1", test_data)
            assert success is True, "Failed to set JSON"
            
            # Retrieve data
            retrieved = redis_manager.get_json("test:user:1")
            assert retrieved is not None, "Failed to get JSON"
            assert retrieved["name"] == "Alice", "Name mismatch"
            assert retrieved["age"] == 30, "Age mismatch"
            
            print("[PASS] Dictionary storage works")
        finally:
            # Cleanup
            redis_manager.delete("test:user:1")
    
    def test_set_and_get_json_list(self):
        """Test storing and retrieving list"""
        print("\n[TEST] Set and get list...")
        
        test_data = [1, 2, 3, 4, 5]
        
        try:
            # Store data
            success = redis_manager.set_json("test:list", test_data)
            assert success is True, "Failed to set JSON list"
            
            # Retrieve data
            retrieved = redis_manager.get_json("test:list")
            assert retrieved is not None, "Failed to get JSON list"
            assert retrieved == test_data, "List mismatch"
            
            print("[PASS] List storage works")
        finally:
            # Cleanup
            redis_manager.delete("test:list")
    
    def test_expiration(self):
        """Test key expiration"""
        print("\n[TEST] Key expiration...")
        
        test_data = {"temp": "data"}
        
        try:
            # Store with 2 second expiration
            success = redis_manager.set_json("test:expire", test_data, expire=2)
            assert success is True, "Failed to set JSON with expiration"
            
            # Verify data exists
            retrieved = redis_manager.get_json("test:expire")
            assert retrieved is not None, "Data should exist immediately"
            
            # Wait for expiration
            print("  Waiting 3 seconds for expiration...")
            time.sleep(3)
            
            # Verify data expired
            retrieved = redis_manager.get_json("test:expire")
            assert retrieved is None, "Data should have expired"
            
            print("[PASS] Expiration works")
        finally:
            # Cleanup (though it should be expired)
            redis_manager.delete("test:expire")
    
    def test_delete(self):
        """Test key deletion"""
        print("\n[TEST] Key deletion...")
        
        try:
            # Store data
            test_data = {"delete": "me"}
            redis_manager.set_json("test:delete", test_data)
            
            # Verify exists
            retrieved = redis_manager.get_json("test:delete")
            assert retrieved is not None, "Data should exist before deletion"
            
            # Delete
            success = redis_manager.delete("test:delete")
            assert success is True, "Delete should return True for existing key"
            
            # Verify deleted
            retrieved = redis_manager.get_json("test:delete")
            assert retrieved is None, "Data should not exist after deletion"
            
            # Delete non-existent key
            success = redis_manager.delete("test:nonexistent")
            assert success is False, "Delete should return False for non-existent key"
            
            print("[PASS] Deletion works")
        finally:
            # Cleanup
            redis_manager.delete("test:delete")
    
    def test_get_nonexistent_key(self):
        """Test getting non-existent key"""
        print("\n[TEST] Get non-existent key...")
        
        retrieved = redis_manager.get_json("test:doesnotexist")
        assert retrieved is None, "Non-existent key should return None"
        
        print("[PASS] Non-existent key handling works")


def run_all_tests():
    """Run all tests without pytest"""
    print("\n" + "="*60)
    print("Running Database and Redis Manager Tests")
    print("="*60)
    
    passed_tests = 0
    failed_tests = 0
    
    # Test DatabaseManager
    db_tests = TestDatabaseManager()
    TestDatabaseManager.setup_class()
    
    db_test_methods = [
        ("health_check", db_tests.test_health_check),
        ("create_tables", db_tests.test_create_tables),
        ("get_session_basic", db_tests.test_get_session_basic),
        ("get_session_with_send", db_tests.test_get_session_with_send),
        ("get_transaction_session", db_tests.test_get_transaction_session),
        ("transaction_rollback", db_tests.test_transaction_rollback),
        ("execute_raw_sql", db_tests.test_execute_raw_sql),
    ]
    
    for test_name, test_method in db_test_methods:
        try:
            test_method()
            passed_tests += 1
        except AssertionError as e:
            print(f"\n[FAIL] DatabaseManager.{test_name}: {e}")
            failed_tests += 1
        finally:
            try:
                db_tests.teardown_method(test_method)
            except:
                pass
    
    TestDatabaseManager.teardown_class()
    
    # Test RedisManager
    redis_tests = TestRedisManager()
    TestRedisManager.setup_class()
    
    redis_test_methods = [
        ("health_check", redis_tests.test_health_check),
        ("set_and_get_json_dict", redis_tests.test_set_and_get_json_dict),
        ("set_and_get_json_list", redis_tests.test_set_and_get_json_list),
        ("expiration", redis_tests.test_expiration),
        ("delete", redis_tests.test_delete),
        ("get_nonexistent_key", redis_tests.test_get_nonexistent_key),
    ]
    
    for test_name, test_method in redis_test_methods:
        try:
            test_method()
            passed_tests += 1
        except AssertionError as e:
            print(f"\n[FAIL] RedisManager.{test_name}: {e}")
            failed_tests += 1
        finally:
            try:
                redis_tests.teardown_method(test_method)
            except:
                pass
    
    TestRedisManager.teardown_class()
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Total:  {passed_tests + failed_tests}")
    
    if failed_tests == 0:
        print("\nAll tests passed successfully!")
        return 0
    else:
        print(f"\n{failed_tests} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())