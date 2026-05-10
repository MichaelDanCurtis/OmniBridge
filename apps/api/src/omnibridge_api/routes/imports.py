from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from neo4j import GraphDatabase
from pydantic import BaseModel

from omnibridge_api.settings import settings
from omnibridge_canonical_graph.knowledge_seed import build_vmware_to_azure_knowledge_seed
from omnibridge_canonical_graph.repository import Neo4jGraphRepository
from omnibridge_vmware_to_azure.fixture_loader import load_fixture
from omnibridge_vmware_to_azure.mapper import map_fixture_to_graph


router = APIRouter(prefix="/imports", tags=["imports"])
_REPO_ROOT = Path(__file__).resolve().parents[5]
_VMWARE_FIXTURE_ROOT = _REPO_ROOT / "corridors" / "vmware-to-azure" / "fixtures"


class FixtureImportRequest(BaseModel):
    fixture_path: str
    persist_to_neo4j: bool = False


class FixtureImportResponse(BaseModel):
    nodes: int
    edges: int
    persisted: bool


class KnowledgeSeedImportRequest(BaseModel):
    project_id: str
    tenant_id: str
    persist_to_neo4j: bool = False


@lru_cache(maxsize=1)
def _cached_neo4j_repository(
    uri: str,
    user: str,
    password: str,
) -> Neo4jGraphRepository:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    return Neo4jGraphRepository(driver)


def get_graph_repository() -> Neo4jGraphRepository | None:
    if not settings.neo4j_uri or not settings.neo4j_password:
        return None

    return _cached_neo4j_repository(
        settings.neo4j_uri,
        settings.neo4j_user,
        settings.neo4j_password,
    )


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _resolve_vmware_fixture_path(fixture_path: str) -> Path:
    requested_path = Path(fixture_path)
    if requested_path.is_absolute():
        raise HTTPException(status_code=400, detail="Fixture path must be relative.")

    fixture_root = _VMWARE_FIXTURE_ROOT.resolve()
    candidates = [
        (_REPO_ROOT / requested_path).resolve(),
        (fixture_root / requested_path).resolve(),
    ]

    for candidate in candidates:
        if not _is_relative_to(candidate, fixture_root):
            continue
        if candidate.is_file():
            return candidate
        raise HTTPException(status_code=400, detail="Fixture file does not exist.")

    raise HTTPException(status_code=400, detail="Fixture path is outside the fixture directory.")


@router.post("/vmware-fixture", response_model=FixtureImportResponse)
def import_vmware_fixture(
    request: FixtureImportRequest,
    graph_repository: Annotated[
        Neo4jGraphRepository | None,
        Depends(get_graph_repository),
    ],
) -> FixtureImportResponse:
    fixture = load_fixture(_resolve_vmware_fixture_path(request.fixture_path))
    graph = map_fixture_to_graph(fixture)
    persisted = False

    if request.persist_to_neo4j:
        if graph_repository is None:
            raise HTTPException(status_code=503, detail="Neo4j graph repository is not configured.")

        graph_repository.bootstrap_schema()
        graph_repository.ingest_graph(nodes=graph.nodes, edges=graph.edges)
        persisted = True

    return FixtureImportResponse(
        nodes=len(graph.nodes),
        edges=len(graph.edges),
        persisted=persisted,
    )


@router.post("/knowledge-seed/vmware-to-azure", response_model=FixtureImportResponse)
def import_vmware_to_azure_knowledge_seed(
    request: KnowledgeSeedImportRequest,
    graph_repository: Annotated[
        Neo4jGraphRepository | None,
        Depends(get_graph_repository),
    ],
) -> FixtureImportResponse:
    seed = build_vmware_to_azure_knowledge_seed(
        project_id=request.project_id,
        tenant_id=request.tenant_id,
    )
    persisted = False

    if request.persist_to_neo4j:
        if graph_repository is None:
            raise HTTPException(status_code=503, detail="Neo4j graph repository is not configured.")

        graph_repository.bootstrap_schema()
        graph_repository.ingest_graph(nodes=list(seed.nodes), edges=list(seed.edges))
        persisted = True

    return FixtureImportResponse(
        nodes=len(seed.nodes),
        edges=len(seed.edges),
        persisted=persisted,
    )
