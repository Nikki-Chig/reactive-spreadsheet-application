# reactive_spreadsheet/src/server.py

import logging
import os
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.httpserver
import json
from typing import Dict
from models import CellUpdate, InitialData  # , GetInitialData  # if needed
import duckdb
import redis

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# In-memory data store for simplicity
spreadsheet_data: Dict[str, str] = {}

# Database configuration
DB_FILE = "spreadsheet.db"

# Initialize DuckDB connection and create table if it doesn't exist
conn = duckdb.connect(DB_FILE)
conn.execute(
    """
    CREATE TABLE IF NOT EXISTS spreadsheet (
        row INTEGER,
        col INTEGER,
        value VARCHAR,
        PRIMARY KEY (row, col)
    )
"""
)

# Load existing data from DuckDB into spreadsheet_data
existing_data = conn.execute("SELECT row, col, value FROM spreadsheet").fetchall()
for row, col, value in existing_data:
    key = f"{row}-{col}"
    spreadsheet_data[key] = value

# Configure Redis connection:
# Read the Redis host from an environment variable; default to 'localhost'
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)
REDIS_STREAM_KEY = "spreadsheet_updates"


class EchoWebSocket(tornado.websocket.WebSocketHandler):
    connections = set()

    # Allow all origins (development only)
    def check_origin(self, origin):
        return True

    def open(self):
        logger.info("WebSocket opened from %s", self.request.remote_ip)
        self.connections.add(self)
        try:
            # Send initial data using the InitialData model with model_dump()
            initial_message = InitialData(
                type="initial_data", payload=spreadsheet_data
            ).model_dump()
            self.write_message(json.dumps(initial_message))
        except Exception as e:
            logger.error(f"Error sending initial data: {e}", exc_info=True)

    def on_message(self, message):
        logger.info("Received message: %s", message)
        try:
            data = json.loads(message)
            # Handle "get_initial_data" separately:
            if data.get("type") == "get_initial_data":
                initial_message = InitialData(
                    type="initial_data", payload=spreadsheet_data
                ).model_dump()
                self.write_message(json.dumps(initial_message))
            elif data.get("type") == "update_cell":
                # Validate the update using CellUpdate
                cell_update = CellUpdate.parse_obj(
                    data
                )
                row = cell_update.payload.row
                col = cell_update.payload.col
                value = cell_update.payload.value
                key = f"{row}-{col}"
                spreadsheet_data[key] = value

                # Update DuckDB: insert or update on conflict
                conn.execute(
                    """
                    INSERT INTO spreadsheet (row, col, value)
                    VALUES (?, ?, ?)
                    ON CONFLICT (row, col) DO UPDATE SET value = excluded.value
                    """,
                    (row, col, value),
                )

                # Publish the update to Redis Stream
                update_data = {
                    "type": "update_cell",
                    "row": str(row),
                    "col": str(col),
                    "value": value,
                }
                redis_client.xadd(REDIS_STREAM_KEY, update_data)

                # Also broadcast immediately to connected clients
                update_message = CellUpdate(
                    type="update_cell", payload={"row": row, "col": col, "value": value}
                ).model_dump()
                self.broadcast(json.dumps(update_message))
            else:
                logger.warning("Unknown message type: %s", data.get("type"))
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

    def on_close(self):
        logger.info("WebSocket closed from %s", self.request.remote_ip)
        self.connections.remove(self)

    def broadcast(self, message):
        for conn in self.connections:
            conn.write_message(message)

    @classmethod
    def broadcast_global(cls, message):
        for conn in cls.connections:
            conn.write_message(message)


def process_redis_stream():
    """
    Process new messages from the Redis stream and broadcast them to all clients.
    A simple implementation that reads new messages and deletes them after processing.
    """
    last_id = redis_client.get("last_processed_id") or "0-0"

    try:
        response = redis_client.xread({REDIS_STREAM_KEY: last_id}, count=10, block=1000)
        if response:
            for stream_key, messages in response:
                for message_id, message in messages:
                    broadcast_message = {
                        "type": message.get("type"),
                        "payload": {
                            "row": int(message.get("row", 0)),
                            "col": int(message.get("col", 0)),
                            "value": message.get("value", ""),
                        },
                    }
                    logger.info("Broadcasting from Redis stream: %s", broadcast_message)
                    EchoWebSocket.broadcast_global(json.dumps(broadcast_message))
                    last_id = message_id
                    redis_client.set("last_processed_id", last_id)
                    redis_client.xdel(REDIS_STREAM_KEY, message_id)
    except Exception as e:
        logger.error(f"Error reading from Redis Stream: {e}", exc_info=True)


def make_app():
    return tornado.web.Application(
        [
            (r"/ws", EchoWebSocket),  # Route: /ws for WebSocket connections
        ]
    )


if __name__ == "__main__":
    app = make_app()
    port = 8888
    server = tornado.httpserver.HTTPServer(app)
    server.listen(port, address="0.0.0.0")  # Bind to all interfaces
    logger.info("Tornado WebSocket server is listening on ws://0.0.0.0:%s/ws", port)

    # Schedule a periodic callback every 1 second to check Redis Stream
    periodic_callback = tornado.ioloop.PeriodicCallback(process_redis_stream, 1000)
    periodic_callback.start()

    tornado.ioloop.IOLoop.current().start()
