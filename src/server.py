# reactive_spreadsheet/src/server.py

import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.httpserver
import json
from typing import Dict
from models import CellUpdate, InitialData
import duckdb

# In-memory data store for simplicity
spreadsheet_data: Dict[str, str] = {}

# Database configuration
DB_FILE = "spreadsheet.db"

# Initialize DuckDB connection and create table if not exists
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

    def open(self):
        print("WebSocket opened")
        self.connections.add(self)
        # Send initial data from in-memory store
        initial_message = InitialData(
            type="initial_data", payload=spreadsheet_data
        ).dict()
        self.write_message(json.dumps(initial_message))

    def on_message(self, message):
        print(f"Received message: {message}")
        try:
            data = json.loads(message)
            cell_update = CellUpdate(**data)
            if cell_update.type == "update_cell":
                row = cell_update.payload.get("row")
                col = cell_update.payload.get("col")
                value = cell_update.payload.get("value", "")
                key = f"{row}-{col}"
                spreadsheet_data[key] = value

                # Update the DuckDB database: insert or update on conflict
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
                ).dict()
                self.broadcast(json.dumps(update_message))
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
            (r"/ws", EchoWebSocket),  # Route: /ws for WebSocket connection
        ]
    )


if __name__ == "__main__":
    app = make_app()
    port = 8888
    server = tornado.httpserver.HTTPServer(app)
    server.listen(port)
    print(f"Tornado WebSocket server is listening on ws://localhost:{port}/ws")
    tornado.ioloop.IOLoop.current().start()
