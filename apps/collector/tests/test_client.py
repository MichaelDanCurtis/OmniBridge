import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import StringIO
from pathlib import Path
import sys
import threading
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from omnibridge_collector.cli import main
from omnibridge_collector.client import (
    DEFAULT_HEARTBEAT_PATH_TEMPLATE,
    DEFAULT_REGISTER_PATH,
    CollectorClient,
)


class _RequestRecorder(BaseHTTPRequestHandler):
    requests = []
    next_status = 200
    next_body = {"collector": {"collector_id": "collector-123", "status": "online"}}

    def do_POST(self):
        length = int(self.headers.get("content-length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        self.__class__.requests.append(
            {
                "body": json.loads(body),
                "content_type": self.headers.get("content-type"),
                "path": self.path,
            }
        )
        response = json.dumps(self.__class__.next_body).encode("utf-8")
        self.send_response(self.__class__.next_status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format, *args):
        return


class CollectorClientTests(unittest.TestCase):
    def setUp(self):
        _RequestRecorder.requests = []
        _RequestRecorder.next_status = 200
        _RequestRecorder.next_body = {
            "collector": {"collector_id": "collector-123", "status": "online"}
        }
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _RequestRecorder)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.api_url = f"http://{host}:{port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def test_register_posts_api_contract_payload(self):
        client = CollectorClient(api_url=self.api_url)

        result = client.register(
            collector_id="collector-release1-demo",
            registration_token="token-abc",
            version="0.1.0",
            capabilities=["fixture_discovery", "heartbeat"],
        )

        self.assertEqual(200, result.status_code)
        self.assertEqual(DEFAULT_REGISTER_PATH, _RequestRecorder.requests[0]["path"])
        self.assertEqual("application/json", _RequestRecorder.requests[0]["content_type"])
        self.assertEqual(
            {
                "capabilities": ["fixture_discovery", "heartbeat"],
                "collector_id": "collector-release1-demo",
                "registration_token": "token-abc",
                "version": "0.1.0",
            },
            _RequestRecorder.requests[0]["body"],
        )

    def test_heartbeat_posts_api_contract_payload(self):
        client = CollectorClient(api_url=self.api_url)

        result = client.heartbeat(
            collector_id="collector-release1-demo",
            registration_token="token-abc",
            version="0.1.0",
            capabilities=["heartbeat"],
        )

        self.assertEqual(200, result.status_code)
        self.assertEqual(
            DEFAULT_HEARTBEAT_PATH_TEMPLATE.format(collector_id="collector-release1-demo"),
            _RequestRecorder.requests[0]["path"],
        )
        self.assertEqual(
            {
                "capabilities": ["heartbeat"],
                "registration_token": "token-abc",
                "version": "0.1.0",
            },
            _RequestRecorder.requests[0]["body"],
        )

    def test_http_error_returns_response_status_and_body(self):
        _RequestRecorder.next_status = 404
        _RequestRecorder.next_body = {"detail": "not found"}
        client = CollectorClient(api_url=self.api_url)

        result = client.register(
            collector_id="collector-release1-demo",
            registration_token="token-abc",
            version="0.1.0",
            capabilities=["heartbeat"],
        )

        self.assertEqual(404, result.status_code)
        self.assertEqual({"detail": "not found"}, result.json_body)
        self.assertFalse(result.ok)

    def test_cli_register_prints_status_json(self):
        stdout = StringIO()

        exit_code = main(
            [
                "register",
                "--api-url",
                self.api_url,
                "--collector-id",
                "collector-release1-demo",
                "--registration-token",
                "token-abc",
            ],
            stdout=stdout,
        )

        self.assertEqual(0, exit_code)
        output = json.loads(stdout.getvalue())
        self.assertEqual(200, output["status_code"])
        self.assertTrue(output["ok"])

    def test_cli_heartbeat_prints_status_json(self):
        stdout = StringIO()

        exit_code = main(
            [
                "heartbeat",
                "--api-url",
                self.api_url,
                "--collector-id",
                "collector-release1-demo",
                "--registration-token",
                "token-abc",
                "--capability",
                "heartbeat",
            ],
            stdout=stdout,
        )

        self.assertEqual(0, exit_code)
        output = json.loads(stdout.getvalue())
        self.assertEqual(200, output["status_code"])
        self.assertTrue(output["ok"])


if __name__ == "__main__":
    unittest.main()
