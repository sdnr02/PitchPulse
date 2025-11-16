import json
import logging
import asyncio
from fastapi import WebSocket, WebSocketDisconnect

from app.core.database import get_db, get_async_redis
from app.services.scoring_service import ScoringService
from app.websockets.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)

async def handle_websocket_connection(
    websocket: WebSocket,
    match_id: int,
    manager: ConnectionManager
) -> None:
    """WebSocket endpoints for real-time match updates with heartbeats"""
    # Connecting to the client
    await manager.connect(websocket, match_id)

    try:
        # Sending the initial match data to the client
        db = next(get_db())
        service = ScoringService(db)
        match = service.get_match(match_id)

        if match:
            # Creating initial data payload
            initial_data = {
                "type": "initial",
                "match_id": match.id,
                "tournament_id": match.tournament_id,
                "team1_id": match.team1_id,
                "team2_id": match.team2_id,
                "status": match.status.value,
                "score_data": match.score_data
            }

            # Sending initial data
            await websocket.send_text(json.dumps(initial_data))
            logger.info(f"Sent initial data to client for match {match_id}")

        # Starting heartbeat task
        heartbeat_task = asyncio.create_task(send_heartbeat(websocket, match_id))

        # Keeping the connection alive and listening for messages
        while True:
            try:
                # Receiving messages from client with timeout
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=60.0  # 60 seconds timeout
                )
                
                # Handling different message types
                if data == "pong":
                    # Client responded to ping - connection is alive
                    logger.debug(f"Received pong from match {match_id}")
                    
                elif data == "ping":
                    # Client sent ping - respond with pong
                    await websocket.send_text("pong")
                    logger.debug(f"Responded to ping for match {match_id}")
                    
                else:
                    # Handling other messages if needed
                    logger.debug(f"Received message from match {match_id}: {data}")
                    
            except asyncio.TimeoutError:
                # No message in 60 seconds - connection might be stale
                logger.warning(f"No response from client on match {match_id} for 60 seconds")

    except WebSocketDisconnect:
        # In case Client disconnected
        logger.info(f"Client disconnected from match {match_id}")
        
    except Exception as e:
        # Exception handling block
        logger.error(f"WebSocket error for match {match_id}: {e}", exc_info=True)
        
    finally:
        # Cleanup
        heartbeat_task.cancel()
        await manager.disconnect(websocket, match_id)

async def send_heartbeat(websocket: WebSocket, match_id: int) -> None:
    """Sending periodic pings to keep the connection alive and detect dead connections"""
    try:
        while True:
            # Waiting 30 seconds before sending ping
            await asyncio.sleep(30)

            try:
                # Sending ping to client
                await websocket.send_text("ping")
                logger.debug(f"Sent ping to client for match {match_id}")

            except Exception as e:
                # Failed to send meaning connection is broken
                logger.error(f"Failed to send heartbeat for match {match_id}: {e}")
                break
                
    except asyncio.CancelledError:
        # Task was cancelled meaning its a normal shutdown
        logger.debug(f"Heartbeat task cancelled for match {match_id}")

async def redis_subscriber(manager: ConnectionManager) -> None:
    """Background function that listens to Redis pub/sub and forwards updates to WebSocket clients"""
    # Logging for start-up
    logger.info("Starting async Redis subscriber...")
    
    try:
        # Getting the async Redis client
        redis = await get_async_redis()
        
        # Creating a pubsub object
        pubsub = redis.pubsub()
        
        # Subscribing to all match channels using pattern
        await pubsub.psubscribe("match: *")
        
        logger.info("Async Redis subscriber listening on match: * channels")
        
        # Listening for messages asynchronously
        async for message in pubsub.listen():
            # Checking if this is a pattern message
            if message["type"] == "pmessage":
                # Extracting channel and data
                channel = message["channel"]
                data = message["data"]
                
                # Extracting match_id from channel name (e.g., "match: 123" -> 123)
                try:
                    match_id = int(channel.split(": ")[1])
                    
                    # Broadcasting to all WebSocket clients watching this match
                    await manager.broadcast_to_match(match_id, data)
                    
                except Exception as e:
                    # In case there was error in processing the specific message
                    logger.error(f"Error processing Redis message from {channel}: {e}", exc_info=True)
    
    except Exception as e:
        # Exception handling block
        logger.error(f"Async Redis subscriber error: {e}", exc_info=True)