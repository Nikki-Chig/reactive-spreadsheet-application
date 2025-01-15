import os
import sys

# Ensure the project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import tornado.testing
import tornado.websocket
from src.server import make_app

# Example tests
class TestWebSocket(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        return make_app()

    @tornado.testing.gen_test
    async def test_initial_data(self):
        ws_url = "ws://localhost:%d/ws" % self.get_http_port()
        ws = await tornado.websocket.websocket_connect(ws_url)
        initial_msg = await ws.read_message()
        self.assertIsNotNone(initial_msg, "Expected an initial data message")
        data = json.loads(initial_msg)
        self.assertEqual(data.get("type"), "initial_data")
        self.assertIsInstance(data.get("payload"), dict)
        ws.close()

    @tornado.testing.gen_test
    async def test_update_cell(self):
        ws_url = "ws://localhost:%d/ws" % self.get_http_port()
        ws = await tornado.websocket.websocket_connect(ws_url)
        # Read initial data message first
        await ws.read_message()

        message = {
            "type": "update_cell",
            "payload": {"row": 1, "col": 1, "value": "test_value"}
        }
        ws.write_message(json.dumps(message))
        response_msg = await ws.read_message()
        self.assertIsNotNone(response_msg, "No response received after update")
        response = json.loads(response_msg)
        self.assertEqual(response.get("type"), "update_cell")
        payload = response.get("payload")
        self.assertEqual(payload.get("row"), 1)
        self.assertEqual(payload.get("col"), 1)
        self.assertEqual(payload.get("value"), "test_value")
        ws.close()

if __name__ == '__main__':
    import pytest
    pytest.main()
