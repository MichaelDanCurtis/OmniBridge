from fastapi import FastAPI

from omnibridge_api.routes.analysis import router as analysis_router
from omnibridge_api.routes.approvals import router as approvals_router
from omnibridge_api.routes.artifacts import router as artifacts_router
from omnibridge_api.routes.blueprints import router as blueprints_router
from omnibridge_api.routes.estimates import router as estimates_router
from omnibridge_api.routes.graph import router as graph_router
from omnibridge_api.routes.imports import router as imports_router
from omnibridge_api.routes.workspace import router as workspace_router
from omnibridge_api.settings import settings

app = FastAPI(title=settings.app_name)
app.include_router(imports_router)
app.include_router(graph_router)
app.include_router(estimates_router)
app.include_router(blueprints_router)
app.include_router(analysis_router)
app.include_router(approvals_router)
app.include_router(artifacts_router)
app.include_router(workspace_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
