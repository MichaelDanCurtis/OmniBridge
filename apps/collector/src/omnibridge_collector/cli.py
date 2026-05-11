"""Command-line interface for registering and heartbeating an OmniBridge collector."""

from __future__ import annotations

import argparse
import json
import sys
from typing import IO
from urllib.error import URLError

from omnibridge_collector.client import (
    DEFAULT_HEARTBEAT_PATH_TEMPLATE,
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
        else:
            response = client.heartbeat(
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


def _capabilities_from_args(capabilities: list[str] | None) -> list[str]:
    return capabilities if capabilities else list(DEFAULT_CAPABILITIES)


def _write_status(stdout: IO[str], status: dict[str, object]) -> None:
    stdout.write(json.dumps(status, sort_keys=True))
    stdout.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
