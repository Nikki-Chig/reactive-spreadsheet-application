# reactive_spreadsheet/src/server.py

import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.httpserver
import json
from typing import Dict
from models import CellUpdate, InitialData  # , GetInitialData  # if needed
import duckdb
import redis

# In-memory data store for simplicity
spreadsheet_data: Dict[str, str] = {}

# Database configuration
DB_FILE = "spreadsheet.db"

# Initialize DuckDB connection and create table if it doesn't exist
conn = duckdb.connect(DB_FILE)
conn.execute("""
    CREATE TABLE IF NOT EXISTS spreadsheet (
        row INTEGER,
        col INTEGER,
        value VARCHAR,
        PRIMARY KEY (row, col)
    )
""")

# Load existing data from DuckDB into spreadsheet_data
existing_data = conn.execute("SELECT row, col, value FROM spreadsheet").fetchall()
for row, col, value in existing_data:
    key = f"{row}-{col}"
    spreadsheet_data[key] = value

# Configure Redis connection and stream key
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
REDIS_STREAM_KEY = "spreadsheet_updates"

class EchoWebSocket(tornado.websocket.WebSocketHandler):
    connections = set()

    # Allow all origins (development only)
    def check_origin(self, origin):
        return True

    def open(self):
        print("WebSocket opened")
        self.connections.add(self)
        # Send initial data using the InitialData model with model_dump()
        initial_message = InitialData(type="initial_data", payload=spreadsheet_data).model_dump()
        self.write_message(json.dumps(initial_message))

    def on_message(self, message):
        print(f"Received message: {message}")
        try:
            data = json.loads(message)
            # Handle "get_initial_data" separately:
            if data.get("type") == "get_initial_data":
                initial_message = InitialData(type="initial_data", payload=spreadsheet_data).model_dump()
                self.write_message(json.dumps(initial_message))
            elif data.get("type") == "update_cell":
                # Validate the update using CellUpdate
                cell_update = CellUpdate.parse_obj(data)
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
                    (row, col, value)
                )

                # Publish the update to Redis Stream
                update_data = {
                    "type": "update_cell",
                    "row": str(row),
                    "col": str(col),
                    "value": value
                }
                redis_client.xadd(REDIS_STREAM_KEY, update_data)

                # Also broadcast immediately to connected clients
                update_message = CellUpdate(
                    type="update_cell", payload={"row": row, "col": col, "value": value}
                ).model_dump()
                self.broadcast(json.dumps(update_message))
            else:
                print(f"Unknown message type: {data.get('type')}")
        except Exception as e:
            print(f"Error processing message: {e}")

    def on_close(self):
        print("WebSocket closed")
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
    A simple implementation that reads new messages and broadcasts them.
    """
    # Use a block read with a timeout
    # Starting from the beginning ("0-0") for simplicity. In production, track the last ID.
    last_id = "0-0"
    try:
        response = redis_client.xread({REDIS_STREAM_KEY: last_id}, count=10, block=1000)
        if response:
            for stream_key, messages in response:
                for message_id, message in messages:
                    # Prepare the message to broadcast. Convert row and col back to int.
                    broadcast_message = {
                        "type": message.get("type"),
                        "payload": {
                            "row": int(message.get("row", 0)),
                            "col": int(message.get("col", 0)),
                            "value": message.get("value", "")
                        }
                    }
                    EchoWebSocket.broadcast_global(json.dumps(broadcast_message))
                    # Update last_id (this simple example does not persist last_id)
                    last_id = message_id
    except Exception as e:
        print(f"Error reading from Redis Stream: {e}")

def make_app():
    return tornado.web.Application([
        (r"/ws", EchoWebSocket),  # Route: /ws for WebSocket connections
    ])

if __name__ == "__main__":
    app = make_app()
    port = 8888
    server = tornado.httpserver.HTTPServer(app)
    server.listen(port)
    print(f"Tornado WebSocket server is listening on ws://localhost:{port}/ws")

    # Schedule a periodic callback every 1 second to check Redis Stream
    periodic_callback = tornado.ioloop.PeriodicCallback(process_redis_stream, 1000)
    periodic_callback.start()

    tornado.ioloop.IOLoop.current().start()
