import os

from pydantic import BaseModel


class ApiSettings(BaseModel):
    app_name: str = "OmniBridge API"
    neo4j_uri: str | None = None
    neo4j_user: str = "neo4j"
    neo4j_password: str | None = None


def load_settings() -> ApiSettings:
    return ApiSettings(
        neo4j_uri=os.getenv("OMNIBRIDGE_NEO4J_URI") or os.getenv("NEO4J_URI"),
        neo4j_user=os.getenv("OMNIBRIDGE_NEO4J_USER") or os.getenv("NEO4J_USER", "neo4j"),
        neo4j_password=os.getenv("OMNIBRIDGE_NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD"),
    )


settings = load_settings()
