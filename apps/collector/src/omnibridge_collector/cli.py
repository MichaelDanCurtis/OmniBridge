"""Command-line interface for registering and heartbeating an OmniBridge collector."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import IO
from urllib.error import URLError

from omnibridge_collector.client import (
    DEFAULT_HEARTBEAT_PATH_TEMPLATE,
    DEFAULT_JOB_CLAIM_PATH_TEMPLATE,
    DEFAULT_JOB_COMPLETE_PATH_TEMPLATE,
    DEFAULT_REGISTER_PATH,
    CollectorClient,
)
from omnibridge_collector.vcenter_connector import (
    VCenterCollectionError,
    VCenterConnectionConfig,
    collect_vcenter_fixture,
)
from omnibridge_vmware_to_azure.discovery_artifact import (
    build_discovery_artifact_from_fixture_payload,
    build_discovery_artifact_from_release1_fixture,
)


DEFAULT_VERSION = "0.1.0"
DEFAULT_CAPABILITIES = ["fixture_discovery", "heartbeat"]
DEFAULT_POLL_INTERVAL_SECONDS = 2.0


class CollectorExecutionError(Exception):
    """Raised when local collector work cannot be completed safely."""


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
        elif args.command == "run-once":
            response = _run_once(
                client=client,
                collector_id=args.collector_id,
                registration_token=args.registration_token,
                version=args.version,
                capabilities=capabilities,
            )
        else:
            return _run(
                client=client,
                collector_id=args.collector_id,
                registration_token=args.registration_token,
                version=args.version,
                capabilities=capabilities,
                max_iterations=args.max_iterations,
                poll_interval_seconds=args.poll_interval_seconds,
                stdout=stdout,
            )
    except URLError as error:
        _write_status(stdout, {"body": str(error), "ok": False, "status_code": 0})
        return 1
    except CollectorExecutionError as error:
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

    run = subparsers.add_parser("run", help="register and continuously run collector jobs")
    _add_common_args(run)
    run.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="maximum poll iterations before exiting; defaults to unlimited",
    )
    run.add_argument(
        "--poll-interval-seconds",
        type=float,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help="seconds to wait between successful poll iterations",
    )

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
        result=_discovery_result(parameters),
    )


def _run(
    *,
    client: CollectorClient,
    collector_id: str,
    registration_token: str,
    version: str,
    capabilities: list[str],
    max_iterations: int | None,
    poll_interval_seconds: float,
    stdout: IO[str],
) -> int:
    registration = client.register(
        collector_id=collector_id,
        registration_token=registration_token,
        version=version,
        capabilities=capabilities,
    )
    _write_status(stdout, registration.status())
    if not registration.ok:
        return 1

    iteration = 0
    while max_iterations is None or iteration < max_iterations:
        response = _run_once(
            client=client,
            collector_id=collector_id,
            registration_token=registration_token,
            version=version,
            capabilities=capabilities,
        )
        _write_status(stdout, response.status())
        if not response.ok:
            return 1

        iteration += 1
        if max_iterations is not None and iteration >= max_iterations:
            break
        time.sleep(poll_interval_seconds)

    return 0


def _discovery_result(parameters: dict[str, object]) -> dict[str, object]:
    source_mode = str(parameters.get("source_mode", "fixture"))
    if source_mode == "vcenter":
        return _vcenter_discovery_result(parameters)
    return _fixture_discovery_result(parameters)


def _fixture_discovery_result(parameters: dict[str, object]) -> dict[str, object]:
    source = str(parameters.get("source", "collector"))
    fixture_path = parameters.get("fixture_path")
    if isinstance(fixture_path, str) and fixture_path:
        path = _resolve_fixture_path(fixture_path)
        if path is None:
            raise CollectorExecutionError(
                f"Fixture path could not be resolved: {fixture_path}"
            )
        artifact = build_discovery_artifact_from_release1_fixture(path)
        return _discovery_result_from_artifact(
            artifact.model_dump(mode="json"),
            source=source,
            completion_message="Fixture discovery artifact collected.",
        )

    return {
        "source": source,
        "compute_nodes": 3,
        "network_segments": 3,
        "graph_nodes": 12,
        "graph_edges": 13,
        "estimate_ready": True,
    }


def _vcenter_discovery_result(parameters: dict[str, object]) -> dict[str, object]:
    try:
        fixture = collect_vcenter_fixture(
            VCenterConnectionConfig(
                vcenter=str(parameters.get("vcenter", "")),
                credential_ref=str(parameters.get("credential_ref", "")),
                project_id=str(parameters.get("project_id", "project-release1-vmware-azure")),
                tenant_id=str(parameters.get("tenant_id", "tenant-omnibridge-demo")),
                datacenter=str(parameters.get("datacenter", "DC1")),
            )
        )
    except VCenterCollectionError as error:
        raise CollectorExecutionError(str(error)) from error

    artifact = build_discovery_artifact_from_fixture_payload(
        fixture,
        source_mode="vcenter",
    )
    return _discovery_result_from_artifact(
        artifact.model_dump(mode="json"),
        source=str(parameters.get("source", "collector")),
        completion_message="vCenter discovery artifact collected.",
    )


def _discovery_result_from_artifact(
    artifact: dict[str, object],
    *,
    source: str,
    completion_message: str,
) -> dict[str, object]:
    summary = artifact.get("summary")
    summary = summary if isinstance(summary, dict) else {}
    return {
        "source": source,
        "compute_nodes": int(summary.get("compute_nodes", 0)),
        "network_segments": int(summary.get("network_segments", 0)),
        "graph_nodes": int(summary.get("graph_nodes", 0)),
        "graph_edges": int(summary.get("graph_edges", 0)),
        "estimate_ready": True,
        "discovery_artifact": artifact,
        "log_events": [
            {
                "stage": "discovery",
                "status": "completed",
                "message": completion_message,
            }
        ],
    }


def _resolve_fixture_path(fixture_path: str) -> Path | None:
    path = Path(fixture_path)
    candidates = [path] if path.is_absolute() else [Path.cwd() / path]
    if not path.is_absolute():
        candidates.extend(parent / path for parent in Path(__file__).resolve().parents)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _capabilities_from_args(capabilities: list[str] | None) -> list[str]:
    return capabilities if capabilities else list(DEFAULT_CAPABILITIES)


def _write_status(stdout: IO[str], status: dict[str, object]) -> None:
    stdout.write(json.dumps(status, sort_keys=True))
    stdout.write("\n")
    stdout.flush()


if __name__ == "__main__":
    raise SystemExit(main())
