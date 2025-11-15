# Warning: This file was AI generated

import logging

from app.core.logging_config import setup_logging

print("=" * 60)
print("LOGGING TEST")
print("=" * 60)

# Setting up the logging
setup_logging(log_level="DEBUG")

# Getting a logger for this test module
logger = logging.getLogger(__name__)

print("\n=== Test 1: Different Log Levels ===\n")

# Testing DEBUG level (cyan)
logger.debug("This is a DEBUG message - should be CYAN")

# Testing INFO level (green)
logger.info("This is an INFO message - should be GREEN")

# Testing WARNING level (yellow)
logger.warning("This is a WARNING message - should be YELLOW")

# Testing ERROR level (red)
logger.error("This is an ERROR message - should be RED")

# Testing CRITICAL level (red on white background)
logger.critical("This is a CRITICAL message - should be RED on WHITE")

print("\n=== Test 2: Logging from Different Modules ===\n")

# Creating loggers with different names to simulate different modules
service_logger = logging.getLogger("app.services.scoring_service")
service_logger.info("Log from scoring service")

api_logger = logging.getLogger("app.main")
api_logger.info("Log from main API")

db_logger = logging.getLogger("app.core.database")
db_logger.warning("Database connection warning")

print("\n=== Test 3: Exception Logging ===\n")

try:
    # Simulating an error
    result = 10 / 0
except Exception as e:
    # Logging with exception info (includes stack trace)
    logger.error("An error occurred during division", exc_info=True)

print("\n=== Test 4: Multi-line Messages ===\n")

logger.info("Processing match data...")
logger.info("Match ID: 123")
logger.info("Team 1: Mumbai Indians")
logger.info("Team 2: Chennai Super Kings")
logger.info("Score: 45/2 in 5.3 overs")

print("\n=== Test 5: Formatted Messages ===\n")

match_id = 456
score = 89
wickets = 3
overs = 10.2

logger.info(f"Match {match_id}: Score is {score}/{wickets} in {overs} overs")
logger.warning(f"Match {match_id} is taking longer than expected")
logger.error(f"Failed to update match {match_id}")

print("\n" + "=" * 60)
print("TEST COMPLETE!")
print("=" * 60)
print("\n[PASS] Check the COLORS in your terminal above!")
print("[PASS] Check 'logs/pitchpulse.log' file (should have plain text, no colors)")
print("\n[CHECK] Log file location: backend/logs/pitchpulse.log")