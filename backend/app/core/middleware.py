import time
import logging

from fastapi import Request

# Getting the logger for this module
logger = logging.getLogger(__name__)

async def log_requests(request: Request, call_next):
    """Middleware to log all incoming requests and their response times"""
    # Logging the incoming request
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    
    # Recording the start time
    start_time = time.time()
    
    # Processing the request
    response = await call_next(request)
    
    # Calculating the duration
    duration = time.time() - start_time
    
    # Logging the response
    logger.info(
        f"Completed: {request.method} {request.url.path} "
        f"Status: {response.status_code} Duration: {duration:.3f}s"
    )
    
    return response