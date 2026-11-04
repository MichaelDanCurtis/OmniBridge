from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any

from omnibridge_api.settings import settings


@dataclass(frozen=True)
class StoredCollector:
    project_id: str
    collector_id: str
    status: str
    vcenter: str
    last_heartbeat_at: str | None
    version: str | None
    capabilities: list[str]


@dataclass(frozen=True)
class StoredRun:
    run_id: str
    project_id: str
    run_type: str
    status: str
    collector_id: str | None
    started_at: str
    completed_at: str | None
    result: dict[str, Any]
    error: str | None


class InvalidRegistrationTokenError(RuntimeError):
    pass


class CollectorNotFoundError(RuntimeError):
    pass


class RunNotFoundError(RuntimeError):
    pass


class RunTransitionError(RuntimeError):
    pass


class ControlPlaneStore:
    def __init__(self, db_path: str | Path = settings.control_plane_db_path) -> None:
        self.db_path = Path(db_path)

    def reset(self) -> None:
        with self._connect() as connection:
            self._ensure_schema(connection)
            connection.execute("DELETE FROM runs")
            connection.execute("DELETE FROM collectors")

    def get_collector(self, collector_id: str) -> StoredCollector | None:
        with self._connect() as connection:
            self._ensure_schema(connection)
            row = connection.execute(
                """
                SELECT project_id, collector_id, status, vcenter, last_heartbeat_at,
                       version, capabilities_json
                FROM collectors
                WHERE collector_id = ?
                """,
                (collector_id,),
            ).fetchone()
        if row is None:
            return None
        return _collector_from_row(row)

    def bootstrap_collector(
        self,
        *,
        project_id: str,
        collector_id: str,
        vcenter: str,
        registration_token: str,
    ) -> StoredCollector:
        now = utc_now()
        with self._connect() as connection:
            self._ensure_schema(connection)
            connection.execute("DELETE FROM runs WHERE project_id = ?", (project_id,))
            connection.execute(
                """
                INSERT INTO collectors (
                    project_id, collector_id, status, vcenter, registration_token_hash,
                    token_created_at, last_heartbeat_at, version, capabilities_json, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?)
                ON CONFLICT(collector_id) DO UPDATE SET
                    project_id = excluded.project_id,
                    status = excluded.status,
                    vcenter = excluded.vcenter,
                    registration_token_hash = excluded.registration_token_hash,
                    token_created_at = excluded.token_created_at,
                    last_heartbeat_at = NULL,
                    version = NULL,
                    capabilities_json = excluded.capabilities_json,
                    updated_at = excluded.updated_at
                """,
                (
                    project_id,
                    collector_id,
                    "pending_registration",
                    vcenter,
                    _hash_token(registration_token),
                    now,
                    json.dumps([]),
                    now,
                ),
            )
        stored = self.get_collector(collector_id)
        if stored is None:
            raise CollectorNotFoundError(collector_id)
        return stored

    def register_collector(
        self,
        *,
        collector_id: str,
        registration_token: str,
        version: str,
        capabilities: list[str],
    ) -> StoredCollector:
        self._assert_valid_token(collector_id, registration_token)
        return self._mark_collector_online(
            collector_id=collector_id,
            version=version,
            capabilities=capabilities,
        )

    def record_collector_heartbeat(
        self,
        *,
        collector_id: str,
        registration_token: str,
        version: str,
        capabilities: list[str],
    ) -> StoredCollector:
        self._assert_valid_token(collector_id, registration_token)
        return self._mark_collector_online(
            collector_id=collector_id,
            version=version,
            capabilities=capabilities,
        )

    def record_run(
        self,
        *,
        run_id: str,
        project_id: str,
        run_type: str,
        status: str,
        collector_id: str | None,
        result: dict[str, Any],
        error: str | None = None,
    ) -> StoredRun:
        now = utc_now()
        completed_at = now if status in {"completed", "failed"} else None
        with self._connect() as connection:
            self._ensure_schema(connection)
            connection.execute(
                """
                INSERT INTO runs (
                    run_id, project_id, run_type, status, collector_id, started_at,
                    completed_at, result_json, error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    status = excluded.status,
                    completed_at = excluded.completed_at,
                    result_json = excluded.result_json,
                    error = excluded.error
                """,
                (
                    run_id,
                    project_id,
                    run_type,
                    status,
                    collector_id,
                    now,
                    completed_at,
                    json.dumps(result, sort_keys=True),
                    error,
                ),
            )
        stored = self.get_run(run_id)
        if stored is None:
            raise RuntimeError(f"Run was not recorded: {run_id}")
        return stored

    def claim_next_run(
        self,
        *,
        project_id: str,
        collector_id: str,
        registration_token: str,
        version: str,
        capabilities: list[str],
    ) -> StoredRun | None:
        self._assert_valid_token(collector_id, registration_token)
        self._mark_collector_online(
            collector_id=collector_id,
            version=version,
            capabilities=capabilities,
        )
        with self._connect() as connection:
            self._ensure_schema(connection)
            row = connection.execute(
                """
                SELECT run_id, result_json
                FROM runs
                WHERE project_id = ? AND status = ?
                ORDER BY started_at ASC
                LIMIT 1
                """,
                (project_id, "queued"),
            ).fetchone()
            if row is None:
                return None

            run_id = row["run_id"]
            result = json.loads(row["result_json"] or "{}")
            result["log_events"] = _append_unique_event(
                result.get("log_events"),
                {
                    "stage": "running",
                    "status": "running",
                    "message": "Collector claimed discovery run.",
                },
            )
            connection.execute(
                """
                UPDATE runs
                SET status = ?, collector_id = ?, result_json = ?
                WHERE run_id = ?
                """,
                ("running", collector_id, json.dumps(result, sort_keys=True), run_id),
            )

        return self.get_run(run_id)

    def complete_run(
        self,
        *,
        run_id: str,
        collector_id: str,
        registration_token: str,
        version: str,
        capabilities: list[str],
        result: dict[str, Any],
    ) -> StoredRun:
        self._assert_valid_token(collector_id, registration_token)
        self._mark_collector_online(
            collector_id=collector_id,
            version=version,
            capabilities=capabilities,
        )
        now = utc_now()
        with self._connect() as connection:
            self._ensure_schema(connection)
            cursor = connection.execute(
                """
                UPDATE runs
                SET status = ?, collector_id = ?, completed_at = ?, result_json = ?, error = NULL
                WHERE run_id = ? AND collector_id = ? AND status = ?
                """,
                (
                    "completed",
                    collector_id,
                    now,
                    json.dumps(result, sort_keys=True),
                    run_id,
                    collector_id,
                    "running",
                ),
            )
        if cursor.rowcount == 0:
            if self.get_run(run_id) is None:
                raise RunNotFoundError(run_id)
            raise RunTransitionError(run_id)

        stored = self.get_run(run_id)
        if stored is None:
            raise RunNotFoundError(run_id)
        return stored

    def get_run(self, run_id: str) -> StoredRun | None:
        with self._connect() as connection:
            self._ensure_schema(connection)
            row = connection.execute(
                """
                SELECT run_id, project_id, run_type, status, collector_id, started_at,
                       completed_at, result_json, error
                FROM runs
                WHERE run_id = ?
                """,
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        return StoredRun(
            run_id=row["run_id"],
            project_id=row["project_id"],
            run_type=row["run_type"],
            status=row["status"],
            collector_id=row["collector_id"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            result=json.loads(row["result_json"] or "{}"),
            error=row["error"],
        )

    def _mark_collector_online(
        self,
        *,
        collector_id: str,
        version: str,
        capabilities: list[str],
    ) -> StoredCollector:
        now = utc_now()
        with self._connect() as connection:
            self._ensure_schema(connection)
            connection.execute(
                """
                UPDATE collectors
                SET status = ?, last_heartbeat_at = ?, version = ?,
                    capabilities_json = ?, updated_at = ?
                WHERE collector_id = ?
                """,
                (
                    "online",
                    now,
                    version,
                    json.dumps(capabilities),
                    now,
                    collector_id,
                ),
            )
        stored = self.get_collector(collector_id)
        if stored is None:
            raise CollectorNotFoundError(collector_id)
        return stored

    def _assert_valid_token(self, collector_id: str, registration_token: str) -> None:
        with self._connect() as connection:
            self._ensure_schema(connection)
            row = connection.execute(
                """
                SELECT registration_token_hash
                FROM collectors
                WHERE collector_id = ?
                """,
                (collector_id,),
            ).fetchone()
        if row is None:
            raise CollectorNotFoundError(collector_id)
        if row["registration_token_hash"] != _hash_token(registration_token):
            raise InvalidRegistrationTokenError("Invalid collector registration token.")

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS collectors (
                collector_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                status TEXT NOT NULL,
                vcenter TEXT NOT NULL,
                registration_token_hash TEXT,
                token_created_at TEXT,
                last_heartbeat_at TEXT,
                version TEXT,
                capabilities_json TEXT NOT NULL DEFAULT '[]',
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                run_type TEXT NOT NULL,
                status TEXT NOT NULL,
                collector_id TEXT,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                result_json TEXT NOT NULL DEFAULT '{}',
                error TEXT
            )
            """
        )


def default_store() -> ControlPlaneStore:
    return ControlPlaneStore()


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _collector_from_row(row: sqlite3.Row) -> StoredCollector:
    return StoredCollector(
        project_id=row["project_id"],
        collector_id=row["collector_id"],
        status=row["status"],
        vcenter=row["vcenter"],
        last_heartbeat_at=row["last_heartbeat_at"],
        version=row["version"],
        capabilities=json.loads(row["capabilities_json"] or "[]"),
    )


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _append_unique_event(
    existing_events: Any,
    event: dict[str, object],
) -> list[dict[str, object]]:
    events = [
        existing_event
        for existing_event in (existing_events if isinstance(existing_events, list) else [])
        if isinstance(existing_event, dict)
    ]
    if event not in events:
        events.append(event)
    return events
