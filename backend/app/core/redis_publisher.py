import json
import logging
from typing import Dict

import redis

logger = logging.getLogger(__name__)

class RedisPublisher:

    def __init__(self, redis_client: redis.Redis) -> None:
        """Initializing the Redis Publisher"""
        self.redis_client = redis_client

    def publish_match_update(
        self,
        match_id: int,
        match_data: Dict
    ) -> None:
        """Publishes a match update to the Redis channel for that match"""
        try:
            # Creating a channel name for this specific match
            channel = f"match: {match_id}"

            # Converting the match data to JSON string
            message = json.dumps(match_data)

            # Publishing the message to the Redis channel
            self.redis_client.publish(channel=channel, message=message)

            # Logging the successful publishing of the message
            logger.info(f"Published the update to the channel")

        except Exception as e:
            # Exception Handling block
            logger.error(f"Failed to publish the match update due to an error: \n{e}", exc_info=True)
    
    def publish_tournament_update(
        self,
        tournament_id: int,
        event_type: str,
        data: Dict
    ) -> None:
        """Publishes a tournament level update to Redis"""
        try:
            # Creating a channel name for this tournament
            channel = f"tournament: {tournament_id}"

            # Creating the event message with the type and the date
            message_data = {
                "event_type": event_type,
                "data": data
            }

            # Converting to the JSON string
            message = json.dumps(message_data)

            # Publishing the message to Redis
            self.redis_client.publish(channel, message)
            
            # Logging the successful publishing of the message
            logger.info(f"Published {event_type} to {channel}")
            
        except Exception as e:
            # Exception handling block
            logger.error(f"Failed to publish tournament update: {e}", exc_info=True)