"""HTTP client for the standalone OmniBridge collector."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


DEFAULT_REGISTER_PATH = "/collectors/release1-demo/register"
DEFAULT_HEARTBEAT_PATH_TEMPLATE = "/collectors/{collector_id}/heartbeat"
DEFAULT_JOB_CLAIM_PATH_TEMPLATE = "/collectors/{collector_id}/jobs/claim"
DEFAULT_JOB_COMPLETE_PATH_TEMPLATE = "/collectors/{collector_id}/jobs/{job_id}/complete"


@dataclass(frozen=True)
class CollectorResponse:
    status_code: int
    body: str
    json_body: Any | None

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def status(self) -> dict[str, Any]:
        return {
            "body": self.json_body if self.json_body is not None else self.body,
            "ok": self.ok,
            "status_code": self.status_code,
        }


class CollectorClient:
    def __init__(
        self,
        api_url: str,
        register_path: str = DEFAULT_REGISTER_PATH,
        heartbeat_path_template: str = DEFAULT_HEARTBEAT_PATH_TEMPLATE,
        job_claim_path_template: str = DEFAULT_JOB_CLAIM_PATH_TEMPLATE,
        job_complete_path_template: str = DEFAULT_JOB_COMPLETE_PATH_TEMPLATE,
        timeout: float = 10.0,
    ) -> None:
        self.api_url = api_url.rstrip("/")
        self.register_path = _normalize_path(register_path)
        self.heartbeat_path_template = _normalize_path(heartbeat_path_template)
        self.job_claim_path_template = _normalize_path(job_claim_path_template)
        self.job_complete_path_template = _normalize_path(job_complete_path_template)
        self.timeout = timeout

    def register(
        self,
        *,
        collector_id: str,
        registration_token: str,
        version: str,
        capabilities: list[str],
    ) -> CollectorResponse:
        return self._post_json(
            self.register_path,
            {
                "capabilities": capabilities,
                "collector_id": collector_id,
                "registration_token": registration_token,
                "version": version,
            },
        )

    def heartbeat(
        self,
        *,
        collector_id: str,
        registration_token: str,
        version: str,
        capabilities: list[str],
    ) -> CollectorResponse:
        encoded_collector_id = quote(collector_id, safe="")
        path = self.heartbeat_path_template.format(collector_id=encoded_collector_id)
        return self._post_json(
            path,
            {
                "capabilities": capabilities,
                "registration_token": registration_token,
                "version": version,
            },
        )

    def claim_job(
        self,
        *,
        collector_id: str,
        registration_token: str,
        version: str,
        capabilities: list[str],
    ) -> CollectorResponse:
        encoded_collector_id = quote(collector_id, safe="")
        path = self.job_claim_path_template.format(collector_id=encoded_collector_id)
        return self._post_json(
            path,
            {
                "capabilities": capabilities,
                "registration_token": registration_token,
                "version": version,
            },
        )

    def complete_job(
        self,
        *,
        collector_id: str,
        job_id: str,
        registration_token: str,
        version: str,
        capabilities: list[str],
        result: Mapping[str, Any],
    ) -> CollectorResponse:
        encoded_collector_id = quote(collector_id, safe="")
        encoded_job_id = quote(job_id, safe="")
        path = self.job_complete_path_template.format(
            collector_id=encoded_collector_id,
            job_id=encoded_job_id,
        )
        return self._post_json(
            path,
            {
                "capabilities": capabilities,
                "registration_token": registration_token,
                "result": result,
                "version": version,
            },
        )

    def _post_json(self, path: str, payload: Mapping[str, Any]) -> CollectorResponse:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        request = Request(
            f"{self.api_url}{_normalize_path(path)}",
            data=body,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                return _read_response(response.status, response.read())
        except HTTPError as error:
            return _read_response(error.code, error.read())


def _normalize_path(path: str) -> str:
    if path.startswith("/"):
        return path
    return f"/{path}"


def _read_response(status_code: int, response_body: bytes) -> CollectorResponse:
    body = response_body.decode("utf-8")
    return CollectorResponse(
        status_code=status_code,
        body=body,
        json_body=_parse_json(body),
    )


def _parse_json(body: str) -> Any | None:
    if not body:
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None
