from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from omnibridge_agent_tools.analysis_workflow import (
    run_fixture_analysis,
    run_graph_grounded_analysis,
)
from omnibridge_agent_tools.graph_knowledge import GraphKnowledgeTools
from omnibridge_canonical_graph.repository import Neo4jGraphRepository

from omnibridge_api.release1_demo import build_release1_demo
from omnibridge_api.routes.imports import get_graph_repository


router = APIRouter(prefix="/analysis", tags=["analysis"])


def get_analysis_graph_repository() -> Neo4jGraphRepository | None:
    return get_graph_repository()


@router.get("/release1-demo")
def release1_demo_analysis(
    graph_repository: Annotated[
        Neo4jGraphRepository | None,
        Depends(get_analysis_graph_repository),
    ],
    mode: Literal["fixture", "graph"] = "fixture",
) -> dict[str, object]:
    demo = build_release1_demo()
    if mode == "graph":
        if graph_repository is not None:
            return run_graph_grounded_analysis(
                application_name=demo.blueprint.application_name,
                project_id=demo.blueprint.project_id,
                tenant_id=demo.workspace["project"]["tenant_id"],
                graph_tools=GraphKnowledgeTools(graph_repository),
                blocker_count=demo.workspace["summary"]["blockers"],
                warning_count=demo.workspace["summary"]["warnings"],
            ).model_dump()

        fallback = run_fixture_analysis(
            compute_nodes=list(demo.blueprint.compute_node_names),
            blocker_count=demo.workspace["summary"]["blockers"],
            warning_count=demo.workspace["summary"]["warnings"],
        )
        return fallback.model_copy(update={"analysis_source": "fixture_fallback"}).model_dump()

    return demo.analysis.model_dump()
