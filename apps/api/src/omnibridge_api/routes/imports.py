from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from omnibridge_vmware_to_azure.fixture_loader import load_fixture
from omnibridge_vmware_to_azure.mapper import map_fixture_to_graph


router = APIRouter(prefix="/imports", tags=["imports"])


class FixtureImportRequest(BaseModel):
    fixture_path: str


class FixtureImportResponse(BaseModel):
    nodes: int
    edges: int


@router.post("/vmware-fixture", response_model=FixtureImportResponse)
def import_vmware_fixture(request: FixtureImportRequest) -> FixtureImportResponse:
    fixture = load_fixture(Path(request.fixture_path))
    graph = map_fixture_to_graph(fixture)
    return FixtureImportResponse(nodes=len(graph.nodes), edges=len(graph.edges))
