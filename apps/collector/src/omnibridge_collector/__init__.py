"""Standalone OmniBridge collector CLI package."""

from omnibridge_collector.client import (
    DEFAULT_HEARTBEAT_PATH_TEMPLATE,
    DEFAULT_REGISTER_PATH,
    CollectorClient,
    CollectorResponse,
)

__all__ = [
    "CollectorClient",
    "CollectorResponse",
    "DEFAULT_HEARTBEAT_PATH_TEMPLATE",
    "DEFAULT_REGISTER_PATH",
]
