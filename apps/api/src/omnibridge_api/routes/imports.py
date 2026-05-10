from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from omnibridge_vmware_to_azure.fixture_loader import load_fixture
from omnibridge_vmware_to_azure.mapper import map_fixture_to_graph


router = APIRouter(prefix="/imports", tags=["imports"])
_REPO_ROOT = Path(__file__).resolve().parents[5]
_VMWARE_FIXTURE_ROOT = _REPO_ROOT / "corridors" / "vmware-to-azure" / "fixtures"


class FixtureImportRequest(BaseModel):
    fixture_path: str


class FixtureImportResponse(BaseModel):
    nodes: int
    edges: int


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
def import_vmware_fixture(request: FixtureImportRequest) -> FixtureImportResponse:
    fixture = load_fixture(_resolve_vmware_fixture_path(request.fixture_path))
    graph = map_fixture_to_graph(fixture)
    return FixtureImportResponse(nodes=len(graph.nodes), edges=len(graph.edges))
