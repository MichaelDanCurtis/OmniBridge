"""Command-line interface for registering and heartbeating an OmniBridge collector."""

from __future__ import annotations

import argparse
import json
import sys
from typing import IO
from urllib.error import URLError

from omnibridge_collector.client import (
    DEFAULT_HEARTBEAT_PATH_TEMPLATE,
    DEFAULT_JOB_CLAIM_PATH_TEMPLATE,
    DEFAULT_JOB_COMPLETE_PATH_TEMPLATE,
    DEFAULT_REGISTER_PATH,
    CollectorClient,
)


DEFAULT_VERSION = "0.1.0"
DEFAULT_CAPABILITIES = ["fixture_discovery", "heartbeat"]


def main(argv: list[str] | None = None, stdout: IO[str] = sys.stdout) -> int:
    args = _build_parser().parse_args(argv)
    client = CollectorClient(
        api_url=args.api_url,
        register_path=args.register_path,
        heartbeat_path_template=args.heartbeat_path_template,
        job_claim_path_template=args.job_claim_path_template,
        job_complete_path_template=args.job_complete_path_template,
    )
    capabilities = _capabilities_from_args(args.capability)

    try:
        if args.command == "register":
            response = client.register(
                collector_id=args.collector_id,
                registration_token=args.registration_token,
                version=args.version,
                capabilities=capabilities,
            )
        elif args.command == "heartbeat":
            response = client.heartbeat(
                collector_id=args.collector_id,
                registration_token=args.registration_token,
                version=args.version,
                capabilities=capabilities,
            )
        else:
            response = _run_once(
                client=client,
                collector_id=args.collector_id,
                registration_token=args.registration_token,
                version=args.version,
                capabilities=capabilities,
            )
    except URLError as error:
        _write_status(stdout, {"body": str(error), "ok": False, "status_code": 0})
        return 1

    _write_status(stdout, response.status())
    return 0 if response.ok else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omnibridge-collector",
        description="Register and heartbeat a standalone OmniBridge collector.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    register = subparsers.add_parser("register", help="register this collector")
    _add_common_args(register)

    heartbeat = subparsers.add_parser("heartbeat", help="send a collector heartbeat")
    _add_common_args(heartbeat)

    run_once = subparsers.add_parser("run-once", help="claim and execute one collector job")
    _add_common_args(run_once)

    return parser


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--api-url", required=True, help="control-plane API base URL")
    parser.add_argument("--collector-id", required=True, help="collector ID from bootstrap")
    parser.add_argument(
        "--registration-token",
        required=True,
        help="registration token from bootstrap",
    )
    parser.add_argument("--version", default=DEFAULT_VERSION, help="collector version")
    parser.add_argument(
        "--capability",
        action="append",
        default=None,
        help="collector capability; can be repeated",
    )
    parser.add_argument(
        "--register-path",
        default=DEFAULT_REGISTER_PATH,
        help="registration endpoint path",
    )
    parser.add_argument(
        "--heartbeat-path-template",
        default=DEFAULT_HEARTBEAT_PATH_TEMPLATE,
        help="heartbeat endpoint path template; supports {collector_id}",
    )
    parser.add_argument(
        "--job-claim-path-template",
        default=DEFAULT_JOB_CLAIM_PATH_TEMPLATE,
        help="job claim endpoint path template; supports {collector_id}",
    )
    parser.add_argument(
        "--job-complete-path-template",
        default=DEFAULT_JOB_COMPLETE_PATH_TEMPLATE,
        help="job complete endpoint path template; supports {collector_id} and {job_id}",
    )


def _run_once(
    *,
    client: CollectorClient,
    collector_id: str,
    registration_token: str,
    version: str,
    capabilities: list[str],
):
    claim = client.claim_job(
        collector_id=collector_id,
        registration_token=registration_token,
        version=version,
        capabilities=capabilities,
    )
    if not claim.ok:
        return claim

    claim_body = claim.json_body if isinstance(claim.json_body, dict) else {}
    job = claim_body.get("job")
    if not isinstance(job, dict):
        return claim

    job_id = str(job.get("job_id", ""))
    job_type = str(job.get("job_type", ""))
    parameters = job.get("parameters")
    if job_type != "discovery" or not isinstance(parameters, dict):
        return claim

    return client.complete_job(
        collector_id=collector_id,
        job_id=job_id,
        registration_token=registration_token,
        version=version,
        capabilities=capabilities,
        result=_fixture_discovery_result(parameters),
    )


def _fixture_discovery_result(parameters: dict[str, object]) -> dict[str, object]:
    return {
        "source": str(parameters.get("source", "fixture")),
        "compute_nodes": 3,
        "network_segments": 3,
        "graph_nodes": 12,
        "graph_edges": 13,
        "estimate_ready": True,
    }


def _capabilities_from_args(capabilities: list[str] | None) -> list[str]:
    return capabilities if capabilities else list(DEFAULT_CAPABILITIES)


def _write_status(stdout: IO[str], status: dict[str, object]) -> None:
    stdout.write(json.dumps(status, sort_keys=True))
    stdout.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
