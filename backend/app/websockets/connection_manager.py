import logging
from typing import Dict, List

from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    
    def __init__(self):
        """Initializing the connection manager object"""
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        match_id: int
    ) -> None:
        """Method to accept a new WebSocket connection"""
        # Waiting for the acceptance of a websocket
        await websocket.accept()

        try:
            # Matching to the channel name in Redis
            channel = f"match: {match_id}"

            # Adding the connections for this channel if it doesn't exist in the dictionary
            if channel not in self.active_connections:
                self.active_connections[channel] = []

            self.active_connections[channel].append(websocket)

            # Log the new connection success
            logger.info(f"Client connected to {channel}. Total connections: {len(self.active_connections[channel])}")

        except Exception as e:
            # Exception Handling block
            logger.error(f"Error adding connections for {channel}. Due to: \n{e}", exc_info=True)
    
    async def disconnect(
        self,
        websocket: WebSocket,
        match_id: int
    ) -> None:
        """Method for removing a WebSocket connection from the match channel"""
        try:
            # Matching to the channel name in Redis
            channel = f"match: {match_id}"

            # Removing the connection if it exists
            if channel in self.active_connections:
                if websocket in self.active_connections[channel]:
                    self.active_connections[channel].remove(websocket)

                # Cleaning up empty channels
                if len(self.active_connections[channel]) == 0:
                    del self.active_connections[channel]
                
                # Logging the disconnection
                logger.info(f"Client disconnected from {channel}")

            else:
                # Warning message that the channel didn't exist
                logger.warning(f"Channel: {channel} doesn't exist. Skipping...")

        except Exception as e:
            # Exception Handling Block
            logger.error(f"Error disconnecting from the Channel: {channel} due to an error: \n{e}", exc_info=True)

    async def send_personal_message(
        self,
        message: str,
        websocket: WebSocket
    ) -> None:
        """Method for sending a message to a specific WebSocket Client"""
        try:
            # Sending the message to the specific client
            await websocket.send_text(message)
            
        except Exception as e:
            # Exception handling block
            logger.error(f"Failed to send personal message: {e}", exc_info=True)

    async def broadcast_to_match(
        self,
        match_id: int,
        message: str
    ) -> None:
        """Method to broadcast a message to all clients watching a specific match"""
        try:
            # Creating the channel name
            channel = f"match: {match_id}"

            # Checking if there are any connections for this channel
            if channel not in self.active_connections:
                logger.debug(f"No active connections for {channel}")
                return
            
            # Getting the list of connections by creating a shallow copy to avoid modification during iteration
            connections = self.active_connections[channel].copy()

            # Counting successful sends
            successful_sends = 0
            failed_connections = []

            # Broadcasting to all connections
            for websocket in connections:
                try:
                    # Sending the message
                    await websocket.send_text(message)
                    successful_sends = successful_sends + 1
                    
                except Exception as e:
                    # Logging failed send but continuing with others
                    logger.warning(f"Failed to send to a client on {channel}: {e}")
                    failed_connections.append(websocket)

            # Removing failed connections
            for websocket in failed_connections:
                await self.disconnect(websocket, match_id)

            # Logging the broadcast
            logger.info(f"Broadcast to {successful_sends}/{len(connections)} clients on {channel}")

        except Exception as e:
            # Error Handling Block
            logger.error(f"Error broadcasting message for {channel} due to: \n{e}", exc_info=True)