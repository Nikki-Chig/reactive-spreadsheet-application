# reactive_spreadsheet/src/server.py

import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.httpserver
import json
from typing import Dict
from models import CellUpdate, InitialData  # , GetInitialData  # if needed
import duckdb

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


class EchoWebSocket(tornado.websocket.WebSocketHandler):
    connections = set()

    # Override check_origin to allow all origins during development
    def check_origin(self, origin):
        return True

    def open(self):
        print("WebSocket opened")
        self.connections.add(self)
        # Send initial data using the InitialData model with model_dump()
        initial_message = InitialData(
            type="initial_data", payload=spreadsheet_data
        ).model_dump()
        self.write_message(json.dumps(initial_message))

    def on_message(self, message):
        print(f"Received message: {message}")
        try:
            data = json.loads(message)
            # Handle "get_initial_data" separately to avoid validation errors:
            if data.get("type") == "get_initial_data":
                # Simply send the initial data again
                initial_message = InitialData(
                    type="initial_data", payload=spreadsheet_data
                ).model_dump()
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
                    (row, col, value),
                )

                # Broadcast the update to all connected clients
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
    server.listen(port)
    print(f"Tornado WebSocket server is listening on ws://localhost:{port}/ws")
    tornado.ioloop.IOLoop.current().start()
