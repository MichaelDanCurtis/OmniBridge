import os
from pathlib import Path

from pydantic import BaseModel


_REPO_ROOT = Path(__file__).resolve().parents[4]


class ApiSettings(BaseModel):
    app_name: str = "OmniBridge API"
    api_public_url: str = "http://127.0.0.1:8001"
    control_plane_db_path: str = str(_REPO_ROOT / ".omnibridge" / "control-plane.sqlite3")
    neo4j_uri: str | None = None
    neo4j_user: str = "neo4j"
    neo4j_password: str | None = None


def load_settings() -> ApiSettings:
    return ApiSettings(
        api_public_url=os.getenv("OMNIBRIDGE_API_PUBLIC_URL", "http://127.0.0.1:8001"),
        control_plane_db_path=os.getenv(
            "OMNIBRIDGE_CONTROL_PLANE_DB_PATH",
            str(_REPO_ROOT / ".omnibridge" / "control-plane.sqlite3"),
        ),
        neo4j_uri=os.getenv("OMNIBRIDGE_NEO4J_URI") or os.getenv("NEO4J_URI"),
        neo4j_user=os.getenv("OMNIBRIDGE_NEO4J_USER") or os.getenv("NEO4J_USER", "neo4j"),
        neo4j_password=os.getenv("OMNIBRIDGE_NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD"),
    )


settings = load_settings()
