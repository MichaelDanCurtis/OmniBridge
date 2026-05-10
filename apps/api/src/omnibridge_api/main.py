from fastapi import FastAPI

from omnibridge_api.routes.graph import router as graph_router
from omnibridge_api.routes.imports import router as imports_router
from omnibridge_api.settings import settings

app = FastAPI(title=settings.app_name)
app.include_router(imports_router)
app.include_router(graph_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
