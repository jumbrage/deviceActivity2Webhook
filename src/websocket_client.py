import os
import json
import websockets
import asyncio
import aiohttp
import logging
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables and validate them
X_TOKEN_ID = os.getenv('X_TOKEN_ID')
X_TOKEN_VALUE = os.getenv('X_TOKEN_VALUE')
GRAPHQL_WS_URL = os.getenv('GRAPHQL_WS_URL')  # Changed from GRAPHQL_WS_URL
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# Validate environment variables
logger.info(f"X_TOKEN_ID: {'set' if X_TOKEN_ID else 'not set'}")
logger.info(f"X_TOKEN_VALUE: {'set' if X_TOKEN_VALUE else 'not set'}")
logger.info(f"GRAPHQL_WS_URL: {GRAPHQL_WS_URL}")
logger.info(f"WEBHOOK_URL: {WEBHOOK_URL}")

async def connect_to_websocket():
    if not all([X_TOKEN_ID, X_TOKEN_VALUE, GRAPHQL_WS_URL, WEBHOOK_URL]):
        logger.error("Missing required environment variables")
        return
    try:
        logger.info(f"Attempting to connect to WebSocket at {GRAPHQL_WS_URL}")
        async with websockets.connect(
            GRAPHQL_WS_URL,
            extra_headers={
                'x-token-id': X_TOKEN_ID,
                'x-token-value': X_TOKEN_VALUE
            }
        ) as websocket:
            logger.info('Successfully connected to the WebSocket server.')
            
            # Initialize connection
            init_message = {
                'type': 'connection_init',
                'payload': {
                    'x-token-id': X_TOKEN_ID,
                    'x-token-value': X_TOKEN_VALUE
                }
            }
            logger.info("Sending connection init message")
            await websocket.send(json.dumps(init_message))
            
            response = await websocket.recv()
            logger.info(f'Received connection_init response: {response}')
            
            # Check if the connection was acknowledged
            response_data = json.loads(response)
            if response_data.get('type') != 'connection_ack':
                logger.error("Connection not acknowledged by server.")
                return
            
            # Subscribe to detection activity
            subscription_message = {
            "id": "1",
            "type": "subscribe",
            "payload": {
                "query": """
                subscription {
                    detectionActivity(filter: {}) {
                        globalTrackId
                        deviceId
                        tag
                        zoneIds
                        timestamp
                        track {
                            id
                            startTime
                            endTime
                        }
                        createdAt
                        updatedAt
                    }
                }
                """
            }
        }
            logger.info("Sending subscription message")
            await websocket.send(json.dumps(subscription_message))
            logger.info('Subscription message sent.')           
            async for message in websocket:
                data = json.loads(message)
                logger.info(f'Received message: {data}')
                message_type = data.get('type')

                if message_type == 'next':
                    try:
                        detection = data['payload']['data']['detectionActivity']
                        await forward_to_webhook(detection)
                    except KeyError as e:
                        logger.error(f"Key error accessing detection data: {e}")
                elif message_type == 'error':
                    payload = data.get('payload', [])
                    if isinstance(payload, list):
                        for error in payload:
                            message = error.get('message', 'No message provided')
                            locations = error.get('locations', [])
                            classification = error.get('extensions', {}).get('classification', 'No classification')
                            logger.error(f"Subscription error: {message}, Classification: {classification}, Locations: {locations}")
                    else:
                        logger.error(f"Received error from server: {payload}")
                elif message_type == 'connection_error':
                    logger.error(f"Connection error: {data['payload']}")
                else:
                    logger.warning(f"Unhandled message type: {message_type}")

    except websockets.exceptions.InvalidURI as e:
        logger.error(f"Invalid WebSocket URI: {e}")
    except websockets.exceptions.ConnectionClosed as e:
        logger.error(f"WebSocket connection closed: code={e.code}, reason={e.reason}")
    except Exception as e:
        logger.error(f"Connection error: {type(e).__name__}: {e}")

async def forward_to_webhook(detection):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(WEBHOOK_URL, json={'detection': detection}) as response:
                response_text = await response.text()  # Get response text to log it
                if response.status == 200:
                    logger.info(f"Successfully forwarded to webhook. Response: {response_text}")
                else:
                    logger.error(f"Webhook returned status {response.status}. Response: {response_text}")
    except Exception as e:
        logger.error(f"Error forwarding to webhook: {e}")

async def main():
    logger.info("Starting WebSocket client")
    while True:
        try:
            await connect_to_websocket()
        except Exception as e:
            logger.error(f"Main loop error: {e}")
        logger.info("Reconnecting in 5 seconds...")
        await asyncio.sleep(5)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("WebSocket client stopped manually.")