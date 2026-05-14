import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import StringIO
from pathlib import Path
import sys
import tempfile
import threading
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from omnibridge_collector.cli import main
from omnibridge_collector.client import (
    DEFAULT_HEARTBEAT_PATH_TEMPLATE,
    DEFAULT_JOB_CLAIM_PATH_TEMPLATE,
    DEFAULT_JOB_COMPLETE_PATH_TEMPLATE,
    DEFAULT_REGISTER_PATH,
    CollectorClient,
)


class _RequestRecorder(BaseHTTPRequestHandler):
    requests = []
    next_status = 200
    next_body = {"collector": {"collector_id": "collector-123", "status": "online"}}
    response_queue = []

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
        if self.__class__.response_queue:
            status, body = self.__class__.response_queue.pop(0)
        else:
            status, body = self.__class__.next_status, self.__class__.next_body
        response = json.dumps(body).encode("utf-8")
        self.send_response(status)
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
        _RequestRecorder.response_queue = []
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

    def test_claim_job_posts_api_contract_payload(self):
        client = CollectorClient(api_url=self.api_url)

        result = client.claim_job(
            collector_id="collector-release1-demo",
            registration_token="token-abc",
            version="0.1.0",
            capabilities=["fixture_discovery", "heartbeat"],
        )

        self.assertEqual(200, result.status_code)
        self.assertEqual(
            DEFAULT_JOB_CLAIM_PATH_TEMPLATE.format(collector_id="collector-release1-demo"),
            _RequestRecorder.requests[0]["path"],
        )
        self.assertEqual(
            {
                "capabilities": ["fixture_discovery", "heartbeat"],
                "registration_token": "token-abc",
                "version": "0.1.0",
            },
            _RequestRecorder.requests[0]["body"],
        )

    def test_complete_job_posts_api_contract_payload(self):
        client = CollectorClient(api_url=self.api_url)

        result = client.complete_job(
            collector_id="collector-release1-demo",
            job_id="discovery-release1-demo-001",
            registration_token="token-abc",
            version="0.1.0",
            capabilities=["fixture_discovery", "heartbeat"],
            result={
                "source": "fixture",
                "compute_nodes": 3,
                "network_segments": 3,
                "graph_nodes": 12,
                "graph_edges": 13,
                "estimate_ready": True,
            },
        )

        self.assertEqual(200, result.status_code)
        self.assertEqual(
            DEFAULT_JOB_COMPLETE_PATH_TEMPLATE.format(
                collector_id="collector-release1-demo",
                job_id="discovery-release1-demo-001",
            ),
            _RequestRecorder.requests[0]["path"],
        )
        self.assertEqual(
            {
                "capabilities": ["fixture_discovery", "heartbeat"],
                "registration_token": "token-abc",
                "version": "0.1.0",
                "result": {
                    "source": "fixture",
                    "compute_nodes": 3,
                    "network_segments": 3,
                    "graph_nodes": 12,
                    "graph_edges": 13,
                    "estimate_ready": True,
                },
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

    def test_cli_run_once_claims_and_completes_fixture_job(self):
        _RequestRecorder.next_body = {
            "collector": {"collector_id": "collector-123", "status": "online"},
            "job": {
                "job_id": "discovery-release1-demo-001",
                "job_type": "discovery",
                "status": "running",
                "parameters": {
                    "source": "collector",
                    "fixture_path": "corridors/vmware-to-azure/fixtures/release1-small-estate.json",
                },
            },
        }
        stdout = StringIO()

        exit_code = main(
            [
                "run-once",
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
        self.assertEqual(2, len(_RequestRecorder.requests))
        self.assertEqual(
            DEFAULT_JOB_CLAIM_PATH_TEMPLATE.format(collector_id="collector-release1-demo"),
            _RequestRecorder.requests[0]["path"],
        )
        self.assertEqual(
            DEFAULT_JOB_COMPLETE_PATH_TEMPLATE.format(
                collector_id="collector-release1-demo",
                job_id="discovery-release1-demo-001",
            ),
            _RequestRecorder.requests[1]["path"],
        )
        self.assertEqual("collector", _RequestRecorder.requests[1]["body"]["result"]["source"])
        self.assertTrue(json.loads(stdout.getvalue())["ok"])

    def test_cli_run_once_derives_discovery_result_from_fixture_path(self):
        fixture = {
            "clusters": [{"moid": "domain-c1"}],
            "hosts": [{"moid": "host-101", "cluster_moid": "domain-c1"}],
            "datastores": [{"moid": "datastore-11"}],
            "networks": [{"moid": "dvportgroup-120"}, {"moid": "dvportgroup-121"}],
            "vms": [
                {
                    "moid": "vm-101",
                    "host_moid": "host-101",
                    "nics": [{"network_moid": "dvportgroup-120"}],
                    "disks": [
                        {"datastore_moid": "datastore-11"},
                        {"datastore_moid": "datastore-11"},
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = Path(tmpdir) / "estate.json"
            fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
            _RequestRecorder.next_body = {
                "collector": {"collector_id": "collector-123", "status": "online"},
                "job": {
                    "job_id": "discovery-release1-demo-001",
                    "job_type": "discovery",
                    "status": "running",
                    "parameters": {
                        "source": "collector",
                        "fixture_path": str(fixture_path),
                    },
                },
            }
            stdout = StringIO()

            exit_code = main(
                [
                    "run-once",
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
        self.assertEqual(
            {
                "source": "collector",
                "compute_nodes": 1,
                "network_segments": 2,
                "graph_nodes": 8,
                "graph_edges": 7,
                "estimate_ready": True,
            },
            _RequestRecorder.requests[1]["body"]["result"],
        )

    def test_cli_run_once_fails_when_fixture_path_cannot_be_resolved(self):
        _RequestRecorder.next_body = {
            "collector": {"collector_id": "collector-123", "status": "online"},
            "job": {
                "job_id": "discovery-release1-demo-001",
                "job_type": "discovery",
                "status": "running",
                "parameters": {
                    "source": "collector",
                    "fixture_path": "missing/estate.json",
                },
            },
        }
        stdout = StringIO()

        exit_code = main(
            [
                "run-once",
                "--api-url",
                self.api_url,
                "--collector-id",
                "collector-release1-demo",
                "--registration-token",
                "token-abc",
            ],
            stdout=stdout,
        )

        self.assertEqual(1, exit_code)
        self.assertEqual(1, len(_RequestRecorder.requests))
        output = json.loads(stdout.getvalue())
        self.assertEqual(0, output["status_code"])
        self.assertFalse(output["ok"])
        self.assertIn("Fixture path could not be resolved", output["body"])

    def test_cli_run_once_with_no_job_makes_only_claim_request(self):
        _RequestRecorder.next_body = {
            "collector": {"collector_id": "collector-123", "status": "online"},
            "job": None,
        }
        stdout = StringIO()

        exit_code = main(
            [
                "run-once",
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
        self.assertEqual(1, len(_RequestRecorder.requests))
        self.assertEqual(
            DEFAULT_JOB_CLAIM_PATH_TEMPLATE.format(collector_id="collector-release1-demo"),
            _RequestRecorder.requests[0]["path"],
        )
        self.assertTrue(json.loads(stdout.getvalue())["ok"])

    def test_cli_run_once_claim_error_does_not_complete(self):
        _RequestRecorder.next_status = 401
        _RequestRecorder.next_body = {"detail": "Invalid collector registration token."}
        stdout = StringIO()

        exit_code = main(
            [
                "run-once",
                "--api-url",
                self.api_url,
                "--collector-id",
                "collector-release1-demo",
                "--registration-token",
                "wrong-token",
            ],
            stdout=stdout,
        )

        self.assertEqual(1, exit_code)
        self.assertEqual(1, len(_RequestRecorder.requests))
        output = json.loads(stdout.getvalue())
        self.assertEqual(401, output["status_code"])
        self.assertFalse(output["ok"])

    def test_cli_run_registers_then_claims_and_completes_fixture_job(self):
        _RequestRecorder.response_queue = [
            (200, {"collector": {"collector_id": "collector-123", "status": "online"}}),
            (
                200,
                {
                    "collector": {"collector_id": "collector-123", "status": "online"},
                    "job": {
                        "job_id": "discovery-release1-demo-001",
                        "job_type": "discovery",
                        "status": "running",
                        "parameters": {
                            "source": "collector",
                            "fixture_path": "corridors/vmware-to-azure/fixtures/release1-small-estate.json",
                        },
                    },
                },
            ),
            (200, {"job": {"job_id": "discovery-release1-demo-001", "status": "completed"}}),
        ]
        stdout = StringIO()

        exit_code = main(
            [
                "run",
                "--api-url",
                self.api_url,
                "--collector-id",
                "collector-release1-demo",
                "--registration-token",
                "token-abc",
                "--max-iterations",
                "1",
                "--poll-interval-seconds",
                "0",
            ],
            stdout=stdout,
        )

        self.assertEqual(0, exit_code)
        self.assertEqual(
            [
                DEFAULT_REGISTER_PATH,
                DEFAULT_JOB_CLAIM_PATH_TEMPLATE.format(
                    collector_id="collector-release1-demo"
                ),
                DEFAULT_JOB_COMPLETE_PATH_TEMPLATE.format(
                    collector_id="collector-release1-demo",
                    job_id="discovery-release1-demo-001",
                ),
            ],
            [request["path"] for request in _RequestRecorder.requests],
        )
        output = [json.loads(line) for line in stdout.getvalue().splitlines()]
        self.assertEqual(2, len(output))
        self.assertTrue(output[0]["ok"])
        self.assertTrue(output[1]["ok"])

    def test_cli_run_registration_error_does_not_claim(self):
        _RequestRecorder.response_queue = [
            (401, {"detail": "Invalid collector registration token."}),
        ]
        stdout = StringIO()

        exit_code = main(
            [
                "run",
                "--api-url",
                self.api_url,
                "--collector-id",
                "collector-release1-demo",
                "--registration-token",
                "wrong-token",
                "--max-iterations",
                "1",
                "--poll-interval-seconds",
                "0",
            ],
            stdout=stdout,
        )

        self.assertEqual(1, exit_code)
        self.assertEqual(1, len(_RequestRecorder.requests))
        self.assertEqual(DEFAULT_REGISTER_PATH, _RequestRecorder.requests[0]["path"])
        output = json.loads(stdout.getvalue())
        self.assertEqual(401, output["status_code"])
        self.assertFalse(output["ok"])


if __name__ == "__main__":
    unittest.main()
