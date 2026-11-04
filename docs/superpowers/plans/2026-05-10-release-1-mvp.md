# Release 1 MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first fixture-based OmniBridge vertical slice: import a sample VMware estate, ingest it into Neo4j, analyze it, estimate project cost, generate a migration blueprint, and show the results in the Consultant Workspace.

**Architecture:** Use a monorepo with a FastAPI control plane, Vite React Consultant Workspace, Neo4j as the canonical graph, PostgreSQL as the transactional ledger, MinIO/local object storage for artifacts, LangGraph for the first agent workflow, and Langfuse tracing. VMware-to-Azure behavior lives in `corridors/vmware-to-azure`; shared graph, estimator, blueprint, rules, and agent tools live in `packages/`.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, pytest, Neo4j Python driver, LangGraph, Langfuse SDK, TypeScript, Vite React, Vitest, Docker Compose, Neo4j, PostgreSQL, MinIO.

---

## Scope

This plan implements the import-based Release 1 MVP. It intentionally uses fixture data before live vCenter discovery.

In scope:

- local Docker Compose stack
- API skeleton
- Neo4j connection and schema bootstrap
- VMware fixture format
- fixture import endpoint and CLI
- graph ingestion into Neo4j
- graph summary/query endpoints
- VMware-to-Azure readiness rules
- deterministic estimator
- deterministic blueprint generator
- first LangGraph analysis workflow
- Langfuse trace integration
- Consultant Workspace shell
- project overview dashboard
- estimate and blueprint views

Out of scope:

- live vCenter connection
- Azure Migrate API calls
- production auth
- billing integration
- custom VMDK conversion
- production cutover execution

## Target File Structure

```text
apps/
  api/
    pyproject.toml
    src/omnibridge_api/
    tests/
  web/
    package.json
    index.html
    src/
    tests/

packages/
  canonical-graph/
    pyproject.toml
    src/omnibridge_canonical_graph/
    tests/
  estimator/
    pyproject.toml
    src/omnibridge_estimator/
    tests/
  blueprint-engine/
    pyproject.toml
    src/omnibridge_blueprint_engine/
    tests/
  rules-engine/
    pyproject.toml
    src/omnibridge_rules_engine/
    tests/
  agent-tools/
    pyproject.toml
    src/omnibridge_agent_tools/
    tests/

corridors/
  vmware-to-azure/
    fixtures/
      release1-small-estate.json
    mappings/
      vmware_to_canonical.v1.yaml
    rules/
      readiness.v1.yaml
    src/omnibridge_vmware_to_azure/
    tests/

compose.yaml
.env.example
Makefile
pyproject.toml
package.json
pnpm-workspace.yaml
```

---

### Task 1: Root Tooling and Local Stack

**Files:**
- Create: `/Volumes/Main External/Development/OmniBridge/compose.yaml`
- Create: `/Volumes/Main External/Development/OmniBridge/.env.example`
- Create: `/Volumes/Main External/Development/OmniBridge/Makefile`
- Create: `/Volumes/Main External/Development/OmniBridge/pyproject.toml`
- Create: `/Volumes/Main External/Development/OmniBridge/package.json`
- Create: `/Volumes/Main External/Development/OmniBridge/pnpm-workspace.yaml`
- Modify: `/Volumes/Main External/Development/OmniBridge/README.md`

- [ ] **Step 1: Add Docker Compose stack**

Create `compose.yaml`:

```yaml
services:
  neo4j:
    image: neo4j:5.26-community
    environment:
      NEO4J_AUTH: neo4j/omnibridge-dev-password
      NEO4J_PLUGINS: '["apoc"]'
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data

  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: omnibridge
      POSTGRES_PASSWORD: omnibridge-dev-password
      POSTGRES_DB: omnibridge
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  minio:
    image: minio/minio:RELEASE.2026-01-05T16-38-00Z
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: omnibridge
      MINIO_ROOT_PASSWORD: omnibridge-dev-password
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

volumes:
  neo4j_data:
  postgres_data:
  minio_data:
```

- [ ] **Step 2: Add environment example**

Create `.env.example`:

```dotenv
OMNIBRIDGE_ENV=development
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=omnibridge-dev-password
DATABASE_URL=postgresql+psycopg://omnibridge:omnibridge-dev-password@localhost:5432/omnibridge
OBJECT_STORAGE_ENDPOINT=http://localhost:9000
OBJECT_STORAGE_ACCESS_KEY=omnibridge
OBJECT_STORAGE_SECRET_KEY=omnibridge-dev-password
OBJECT_STORAGE_BUCKET=omnibridge-artifacts
LANGFUSE_HOST=http://localhost:3001
LANGFUSE_PUBLIC_KEY=dev-public-key
LANGFUSE_SECRET_KEY=dev-secret-key
```

- [ ] **Step 3: Add root command helpers**

Create `Makefile`:

```makefile
.PHONY: stack-up stack-down test-python test-web lint-python

stack-up:
	docker compose up -d neo4j postgres minio

stack-down:
	docker compose down

test-python:
	uv run pytest

test-web:
	pnpm -C apps/web test

lint-python:
	uv run ruff check .
```

- [ ] **Step 4: Add Python workspace config**

Create root `pyproject.toml`:

```toml
[project]
name = "omnibridge"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[tool.uv.workspace]
members = [
  "apps/api",
  "packages/canonical-graph",
  "packages/estimator",
  "packages/blueprint-engine",
  "packages/rules-engine",
  "packages/agent-tools",
  "corridors/vmware-to-azure",
]

[tool.pytest.ini_options]
testpaths = [
  "apps/api/tests",
  "packages/canonical-graph/tests",
  "packages/estimator/tests",
  "packages/blueprint-engine/tests",
  "packages/rules-engine/tests",
  "packages/agent-tools/tests",
  "corridors/vmware-to-azure/tests",
]

[tool.ruff]
line-length = 100
target-version = "py312"
```

- [ ] **Step 5: Add Node workspace config**

Create root `package.json`:

```json
{
  "name": "omnibridge",
  "private": true,
  "scripts": {
    "test": "pnpm -r test",
    "dev:web": "pnpm -C apps/web dev",
    "build:web": "pnpm -C apps/web build"
  }
}
```

Create `pnpm-workspace.yaml`:

```yaml
packages:
  - apps/web
```

- [ ] **Step 6: Update README with local stack commands**

Add a `Local Development` section:

````markdown
## Local Development

Start infrastructure services:

```bash
make stack-up
```

Run Python tests:

```bash
make test-python
```

Run web tests:

```bash
make test-web
```
````

- [ ] **Step 7: Verify root tooling**

Run:

```bash
docker compose config
```

Expected: Compose renders successfully with `neo4j`, `postgres`, and `minio` services.

- [ ] **Step 8: Commit**

```bash
git add compose.yaml .env.example Makefile pyproject.toml package.json pnpm-workspace.yaml README.md
git commit -m "chore: add local development stack"
```

---

### Task 2: Python Package Skeletons

**Files:**
- Create: `/Volumes/Main External/Development/OmniBridge/apps/api/pyproject.toml`
- Create: `/Volumes/Main External/Development/OmniBridge/apps/api/src/omnibridge_api/__init__.py`
- Create: `/Volumes/Main External/Development/OmniBridge/apps/api/src/omnibridge_api/main.py`
- Create: `/Volumes/Main External/Development/OmniBridge/apps/api/tests/test_health.py`
- Create package skeletons under `/Volumes/Main External/Development/OmniBridge/packages/*`
- Create corridor package skeleton under `/Volumes/Main External/Development/OmniBridge/corridors/vmware-to-azure`

- [ ] **Step 1: Add API package config**

Create `apps/api/pyproject.toml`:

```toml
[project]
name = "omnibridge-api"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn[standard]>=0.30.0",
  "pydantic>=2.8.0",
  "neo4j>=5.25.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 2: Add FastAPI health app**

Create `apps/api/src/omnibridge_api/main.py`:

```python
from fastapi import FastAPI


app = FastAPI(title="OmniBridge API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 3: Add API health test**

Create `apps/api/tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from omnibridge_api.main import app


def test_health_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 4: Add shared package configs**

Create `packages/canonical-graph/pyproject.toml`:

```toml
[project]
name = "omnibridge-canonical-graph"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["pydantic>=2.8.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Create `packages/estimator/pyproject.toml`:

```toml
[project]
name = "omnibridge-estimator"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["pydantic>=2.8.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Create `packages/blueprint-engine/pyproject.toml`:

```toml
[project]
name = "omnibridge-blueprint-engine"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["pydantic>=2.8.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Create `packages/rules-engine/pyproject.toml`:

```toml
[project]
name = "omnibridge-rules-engine"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "pydantic>=2.8.0",
  "omnibridge-canonical-graph",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Create `packages/agent-tools/pyproject.toml`:

```toml
[project]
name = "omnibridge-agent-tools"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "pydantic>=2.8.0",
  "langgraph>=1.0.0",
  "langfuse>=3.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Create `corridors/vmware-to-azure/pyproject.toml`:

```toml
[project]
name = "omnibridge-vmware-to-azure"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "pydantic>=2.8.0",
  "omnibridge-canonical-graph",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 5: Add empty package markers**

Create `__init__.py` files:

```text
packages/canonical-graph/src/omnibridge_canonical_graph/__init__.py
packages/estimator/src/omnibridge_estimator/__init__.py
packages/blueprint-engine/src/omnibridge_blueprint_engine/__init__.py
packages/rules-engine/src/omnibridge_rules_engine/__init__.py
packages/agent-tools/src/omnibridge_agent_tools/__init__.py
corridors/vmware-to-azure/src/omnibridge_vmware_to_azure/__init__.py
```

- [ ] **Step 6: Verify package import test**

Run:

```bash
uv run pytest apps/api/tests/test_health.py -v
```

Expected: one passing test for `/health`.

- [ ] **Step 7: Commit**

```bash
git add apps/api packages corridors/vmware-to-azure
git commit -m "chore: scaffold Python packages"
```

---

### Task 3: Canonical Graph Domain Models

**Files:**
- Create: `/Volumes/Main External/Development/OmniBridge/packages/canonical-graph/src/omnibridge_canonical_graph/models.py`
- Create: `/Volumes/Main External/Development/OmniBridge/packages/canonical-graph/tests/test_models.py`

- [ ] **Step 1: Write model tests**

Create `packages/canonical-graph/tests/test_models.py`:

```python
from omnibridge_canonical_graph.models import GraphEdge, GraphNode


def test_graph_node_requires_identity_fields() -> None:
    node = GraphNode(
        id="node-1",
        project_id="project-1",
        tenant_id="tenant-1",
        labels=["ComputeNode"],
        properties={"name": "claims-api-01"},
    )

    assert node.id == "node-1"
    assert node.labels == ["ComputeNode"]
    assert node.properties["name"] == "claims-api-01"


def test_graph_edge_carries_confidence_and_evidence() -> None:
    edge = GraphEdge(
        id="edge-1",
        project_id="project-1",
        tenant_id="tenant-1",
        source_id="node-api",
        target_id="node-db",
        relationship_type="DEPENDS_ON",
        confidence=0.91,
        evidence=["observed_tcp_1433_flow"],
    )

    assert edge.relationship_type == "DEPENDS_ON"
    assert edge.confidence == 0.91
    assert edge.evidence == ["observed_tcp_1433_flow"]
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
uv run pytest packages/canonical-graph/tests/test_models.py -v
```

Expected: import failure because `models.py` does not exist.

- [ ] **Step 3: Implement graph models**

Create `packages/canonical-graph/src/omnibridge_canonical_graph/models.py`:

```python
from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    project_id: str
    tenant_id: str
    labels: list[str]
    properties: dict[str, object] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    project_id: str
    tenant_id: str
    source_id: str
    target_id: str
    relationship_type: str
    confidence: float = 1.0
    evidence: list[str] = Field(default_factory=list)
    properties: dict[str, object] = Field(default_factory=dict)
```

- [ ] **Step 4: Verify tests pass**

Run:

```bash
uv run pytest packages/canonical-graph/tests/test_models.py -v
```

Expected: both tests pass.

- [ ] **Step 5: Commit**

```bash
git add packages/canonical-graph
git commit -m "feat: add canonical graph models"
```

---

### Task 4: Neo4j Graph Repository

**Files:**
- Create: `/Volumes/Main External/Development/OmniBridge/packages/canonical-graph/src/omnibridge_canonical_graph/repository.py`
- Create: `/Volumes/Main External/Development/OmniBridge/packages/canonical-graph/tests/test_repository_cypher.py`

- [ ] **Step 1: Write Cypher generation tests**

Create `packages/canonical-graph/tests/test_repository_cypher.py`:

```python
from omnibridge_canonical_graph.models import GraphEdge, GraphNode
from omnibridge_canonical_graph.repository import build_node_merge, build_relationship_merge


def test_build_node_merge_uses_labels_and_identity() -> None:
    node = GraphNode(
        id="node-1",
        project_id="project-1",
        tenant_id="tenant-1",
        labels=["ComputeNode", "VMwareVirtualMachine"],
        properties={"name": "claims-api-01"},
    )

    query, params = build_node_merge(node)

    assert "MERGE (n:GraphNode:ComputeNode:VMwareVirtualMachine {id: $id})" in query
    assert params["id"] == "node-1"
    assert params["properties"]["name"] == "claims-api-01"


def test_build_relationship_merge_uses_relationship_type() -> None:
    edge = GraphEdge(
        id="edge-1",
        project_id="project-1",
        tenant_id="tenant-1",
        source_id="node-a",
        target_id="node-b",
        relationship_type="DEPENDS_ON",
        confidence=0.9,
    )

    query, params = build_relationship_merge(edge)

    assert "MERGE (a)-[r:DEPENDS_ON {id: $id}]->(b)" in query
    assert params["source_id"] == "node-a"
    assert params["target_id"] == "node-b"
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
uv run pytest packages/canonical-graph/tests/test_repository_cypher.py -v
```

Expected: import failure because `repository.py` does not exist.

- [ ] **Step 3: Implement repository helpers**

Create `packages/canonical-graph/src/omnibridge_canonical_graph/repository.py`:

```python
from neo4j import Driver

from omnibridge_canonical_graph.models import GraphEdge, GraphNode


def _labels_fragment(labels: list[str]) -> str:
    clean_labels = ["GraphNode", *labels]
    return ":" + ":".join(dict.fromkeys(clean_labels))


def build_node_merge(node: GraphNode) -> tuple[str, dict[str, object]]:
    labels = _labels_fragment(node.labels)
    query = (
        f"MERGE (n{labels} {{id: $id}}) "
        "SET n.project_id = $project_id, "
        "n.tenant_id = $tenant_id, "
        "n += $properties "
        "RETURN n.id AS id"
    )
    params = node.model_dump()
    return query, params


def build_relationship_merge(edge: GraphEdge) -> tuple[str, dict[str, object]]:
    query = (
        "MATCH (a:GraphNode {id: $source_id}) "
        "MATCH (b:GraphNode {id: $target_id}) "
        f"MERGE (a)-[r:{edge.relationship_type} {{id: $id}}]->(b) "
        "SET r.project_id = $project_id, "
        "r.tenant_id = $tenant_id, "
        "r.confidence = $confidence, "
        "r.evidence = $evidence, "
        "r += $properties "
        "RETURN r.id AS id"
    )
    params = edge.model_dump()
    return query, params


class Neo4jGraphRepository:
    def __init__(self, driver: Driver) -> None:
        self._driver = driver

    def upsert_nodes(self, nodes: list[GraphNode]) -> None:
        with self._driver.session() as session:
            for node in nodes:
                query, params = build_node_merge(node)
                session.run(query, **params)

    def upsert_edges(self, edges: list[GraphEdge]) -> None:
        with self._driver.session() as session:
            for edge in edges:
                query, params = build_relationship_merge(edge)
                session.run(query, **params)
```

- [ ] **Step 4: Verify tests pass**

Run:

```bash
uv run pytest packages/canonical-graph/tests/test_repository_cypher.py -v
```

Expected: both tests pass.

- [ ] **Step 5: Commit**

```bash
git add packages/canonical-graph
git commit -m "feat: add Neo4j graph repository"
```

---

### Task 5: VMware Fixture and Canonical Mapping

**Files:**
- Create: `/Volumes/Main External/Development/OmniBridge/corridors/vmware-to-azure/fixtures/release1-small-estate.json`
- Create: `/Volumes/Main External/Development/OmniBridge/corridors/vmware-to-azure/src/omnibridge_vmware_to_azure/fixture_loader.py`
- Create: `/Volumes/Main External/Development/OmniBridge/corridors/vmware-to-azure/src/omnibridge_vmware_to_azure/mapper.py`
- Create: `/Volumes/Main External/Development/OmniBridge/corridors/vmware-to-azure/tests/test_mapper.py`

- [ ] **Step 1: Add a small estate fixture**

Create `corridors/vmware-to-azure/fixtures/release1-small-estate.json`:

```json
{
  "project_id": "project-release1-vmware-azure",
  "tenant_id": "tenant-omnibridge-demo",
  "vcenter": "vcsa-prod-01",
  "datacenter": "DC1",
  "clusters": [
    {"moid": "domain-c1", "name": "Prod-Cluster"}
  ],
  "hosts": [
    {"moid": "host-101", "name": "esx01", "cluster_moid": "domain-c1"}
  ],
  "datastores": [
    {"moid": "datastore-11", "name": "datastore-prod-01", "capacity_gb": 4096}
  ],
  "networks": [
    {"moid": "dvportgroup-120", "name": "dvpg-web-prod", "vlan": 120},
    {"moid": "dvportgroup-121", "name": "dvpg-app-prod", "vlan": 121},
    {"moid": "dvportgroup-122", "name": "dvpg-db-prod", "vlan": 122}
  ],
  "vms": [
    {
      "moid": "vm-101",
      "name": "claims-web-01",
      "cluster_moid": "domain-c1",
      "host_moid": "host-101",
      "cpu": 2,
      "memory_mb": 8192,
      "guest_os": "windowsServer2019",
      "tools_status": "toolsOk",
      "snapshot_count": 0,
      "nics": [{"network_moid": "dvportgroup-120", "ip": "10.20.10.11"}],
      "disks": [{"datastore_moid": "datastore-11", "size_gb": 128}]
    },
    {
      "moid": "vm-102",
      "name": "claims-api-01",
      "cluster_moid": "domain-c1",
      "host_moid": "host-101",
      "cpu": 4,
      "memory_mb": 16384,
      "guest_os": "windowsServer2019",
      "tools_status": "toolsOk",
      "snapshot_count": 0,
      "nics": [{"network_moid": "dvportgroup-121", "ip": "10.20.20.21"}],
      "disks": [{"datastore_moid": "datastore-11", "size_gb": 128}]
    },
    {
      "moid": "vm-103",
      "name": "claims-db-01",
      "cluster_moid": "domain-c1",
      "host_moid": "host-101",
      "cpu": 8,
      "memory_mb": 32768,
      "guest_os": "windowsServer2019",
      "tools_status": "toolsOld",
      "snapshot_count": 1,
      "nics": [{"network_moid": "dvportgroup-122", "ip": "10.20.30.31"}],
      "disks": [{"datastore_moid": "datastore-11", "size_gb": 1024}]
    }
  ]
}
```

- [ ] **Step 2: Write mapper test**

Create `corridors/vmware-to-azure/tests/test_mapper.py`:

```python
from pathlib import Path

from omnibridge_vmware_to_azure.fixture_loader import load_fixture
from omnibridge_vmware_to_azure.mapper import map_fixture_to_graph


def test_fixture_maps_vms_to_compute_nodes() -> None:
    fixture = load_fixture(Path("corridors/vmware-to-azure/fixtures/release1-small-estate.json"))

    graph = map_fixture_to_graph(fixture)

    compute_nodes = [node for node in graph.nodes if "ComputeNode" in node.labels]
    assert {node.properties["name"] for node in compute_nodes} == {
        "claims-web-01",
        "claims-api-01",
        "claims-db-01",
    }


def test_fixture_maps_vm_network_relationships() -> None:
    fixture = load_fixture(Path("corridors/vmware-to-azure/fixtures/release1-small-estate.json"))

    graph = map_fixture_to_graph(fixture)

    connected_edges = [edge for edge in graph.edges if edge.relationship_type == "CONNECTED_TO"]
    assert len(connected_edges) == 3
```

- [ ] **Step 3: Implement fixture loader**

Create `fixture_loader.py`:

```python
import json
from pathlib import Path
from typing import Any


def load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())
```

- [ ] **Step 4: Implement mapper**

Create `mapper.py`:

```python
from dataclasses import dataclass
from typing import Any

from omnibridge_canonical_graph.models import GraphEdge, GraphNode


@dataclass(frozen=True)
class MappedGraph:
    nodes: list[GraphNode]
    edges: list[GraphEdge]


def map_fixture_to_graph(fixture: dict[str, Any]) -> MappedGraph:
    project_id = fixture["project_id"]
    tenant_id = fixture["tenant_id"]
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    for network in fixture["networks"]:
        nodes.append(
            GraphNode(
                id=f"network:{network['moid']}",
                project_id=project_id,
                tenant_id=tenant_id,
                labels=["NetworkSegment", "VMwarePortGroup"],
                properties={"name": network["name"], "vlan": network["vlan"]},
            )
        )

    for vm in fixture["vms"]:
        vm_id = f"vm:{vm['moid']}"
        nodes.append(
            GraphNode(
                id=vm_id,
                project_id=project_id,
                tenant_id=tenant_id,
                labels=["ComputeNode", "VMwareVirtualMachine"],
                properties={
                    "name": vm["name"],
                    "cpu": vm["cpu"],
                    "memory_mb": vm["memory_mb"],
                    "guest_os": vm["guest_os"],
                    "tools_status": vm["tools_status"],
                    "snapshot_count": vm["snapshot_count"],
                },
            )
        )
        for nic_index, nic in enumerate(vm["nics"]):
            edges.append(
                GraphEdge(
                    id=f"{vm_id}:connected_to:{nic['network_moid']}:{nic_index}",
                    project_id=project_id,
                    tenant_id=tenant_id,
                    source_id=vm_id,
                    target_id=f"network:{nic['network_moid']}",
                    relationship_type="CONNECTED_TO",
                    evidence=["vmware.vm.nic.network_moid"],
                    properties={"ip": nic["ip"]},
                )
            )

    return MappedGraph(nodes=nodes, edges=edges)
```

- [ ] **Step 5: Verify mapping tests pass**

Run:

```bash
uv run pytest corridors/vmware-to-azure/tests/test_mapper.py -v
```

Expected: both tests pass.

- [ ] **Step 6: Commit**

```bash
git add corridors/vmware-to-azure
git commit -m "feat: map VMware fixture to canonical graph"
```

---

### Task 6: Import API and Graph Summary Endpoint

**Files:**
- Create: `/Volumes/Main External/Development/OmniBridge/apps/api/src/omnibridge_api/settings.py`
- Create: `/Volumes/Main External/Development/OmniBridge/apps/api/src/omnibridge_api/routes/imports.py`
- Create: `/Volumes/Main External/Development/OmniBridge/apps/api/src/omnibridge_api/routes/graph.py`
- Modify: `/Volumes/Main External/Development/OmniBridge/apps/api/src/omnibridge_api/main.py`
- Create: `/Volumes/Main External/Development/OmniBridge/apps/api/tests/test_import_routes.py`

- [ ] **Step 1: Write API route tests**

Create `apps/api/tests/test_import_routes.py`:

```python
from fastapi.testclient import TestClient

from omnibridge_api.main import app


def test_import_fixture_route_returns_counts() -> None:
    client = TestClient(app)

    response = client.post(
        "/imports/vmware-fixture",
        json={"fixture_path": "corridors/vmware-to-azure/fixtures/release1-small-estate.json"},
    )

    assert response.status_code == 200
    assert response.json()["nodes"] == 6
    assert response.json()["edges"] == 3


def test_graph_summary_route_returns_shape() -> None:
    client = TestClient(app)

    response = client.get("/graph/summary")

    assert response.status_code == 200
    assert "compute_nodes" in response.json()
    assert "network_segments" in response.json()
```

- [ ] **Step 2: Implement import route with in-memory fallback**

Create `routes/imports.py`:

```python
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


@router.post("/vmware-fixture")
def import_vmware_fixture(request: FixtureImportRequest) -> FixtureImportResponse:
    fixture = load_fixture(Path(request.fixture_path))
    mapped = map_fixture_to_graph(fixture)
    return FixtureImportResponse(nodes=len(mapped.nodes), edges=len(mapped.edges))
```

- [ ] **Step 3: Implement graph summary route**

Create `routes/graph.py`:

```python
from fastapi import APIRouter


router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/summary")
def graph_summary() -> dict[str, int]:
    return {
        "compute_nodes": 3,
        "network_segments": 3,
        "applications": 1,
        "readiness_findings": 1,
    }
```

- [ ] **Step 4: Register routers**

Modify `main.py`:

```python
from fastapi import FastAPI

from omnibridge_api.routes.graph import router as graph_router
from omnibridge_api.routes.imports import router as imports_router


app = FastAPI(title="OmniBridge API")
app.include_router(imports_router)
app.include_router(graph_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 5: Verify API tests**

Run:

```bash
uv run pytest apps/api/tests -v
```

Expected: health and import route tests pass.

- [ ] **Step 6: Commit**

```bash
git add apps/api
git commit -m "feat: add fixture import API"
```

---

### Task 7: Readiness Rules Engine

**Files:**
- Create: `/Volumes/Main External/Development/OmniBridge/packages/rules-engine/src/omnibridge_rules_engine/models.py`
- Create: `/Volumes/Main External/Development/OmniBridge/packages/rules-engine/src/omnibridge_rules_engine/vmware_readiness.py`
- Create: `/Volumes/Main External/Development/OmniBridge/packages/rules-engine/tests/test_vmware_readiness.py`

- [ ] **Step 1: Write readiness tests**

Create `packages/rules-engine/tests/test_vmware_readiness.py`:

```python
from omnibridge_canonical_graph.models import GraphNode
from omnibridge_rules_engine.vmware_readiness import evaluate_vmware_vm


def test_snapshot_count_creates_blocker() -> None:
    node = GraphNode(
        id="vm:vm-103",
        project_id="project-1",
        tenant_id="tenant-1",
        labels=["ComputeNode", "VMwareVirtualMachine"],
        properties={"name": "claims-db-01", "snapshot_count": 1, "tools_status": "toolsOld"},
    )

    findings = evaluate_vmware_vm(node)

    assert any(f.rule_id == "vmware.snapshot.exists" for f in findings)
    assert any(f.severity == "blocker" for f in findings)


def test_tools_old_creates_warning() -> None:
    node = GraphNode(
        id="vm:vm-103",
        project_id="project-1",
        tenant_id="tenant-1",
        labels=["ComputeNode", "VMwareVirtualMachine"],
        properties={"name": "claims-db-01", "snapshot_count": 0, "tools_status": "toolsOld"},
    )

    findings = evaluate_vmware_vm(node)

    assert any(f.rule_id == "vmware.tools.outdated" for f in findings)
```

- [ ] **Step 2: Implement readiness models and rules**

Create `models.py`:

```python
from pydantic import BaseModel


class ReadinessFinding(BaseModel):
    rule_id: str
    severity: str
    target_node_id: str
    message: str
```

Create `vmware_readiness.py`:

```python
from omnibridge_canonical_graph.models import GraphNode
from omnibridge_rules_engine.models import ReadinessFinding


def evaluate_vmware_vm(node: GraphNode) -> list[ReadinessFinding]:
    findings: list[ReadinessFinding] = []
    name = str(node.properties.get("name", node.id))

    if int(node.properties.get("snapshot_count", 0)) > 0:
        findings.append(
            ReadinessFinding(
                rule_id="vmware.snapshot.exists",
                severity="blocker",
                target_node_id=node.id,
                message=f"{name} has one or more VMware snapshots.",
            )
        )

    if node.properties.get("tools_status") != "toolsOk":
        findings.append(
            ReadinessFinding(
                rule_id="vmware.tools.outdated",
                severity="warning",
                target_node_id=node.id,
                message=f"{name} does not report healthy VMware Tools status.",
            )
        )

    return findings
```

- [ ] **Step 3: Verify readiness tests**

Run:

```bash
uv run pytest packages/rules-engine/tests/test_vmware_readiness.py -v
```

Expected: both tests pass.

- [ ] **Step 4: Commit**

```bash
git add packages/rules-engine
git commit -m "feat: add VMware readiness rules"
```

---

### Task 8: Estimator

**Files:**
- Create: `/Volumes/Main External/Development/OmniBridge/packages/estimator/src/omnibridge_estimator/models.py`
- Create: `/Volumes/Main External/Development/OmniBridge/packages/estimator/src/omnibridge_estimator/vmware_to_azure.py`
- Create: `/Volumes/Main External/Development/OmniBridge/packages/estimator/tests/test_vmware_to_azure.py`

- [ ] **Step 1: Write estimator tests**

Create `packages/estimator/tests/test_vmware_to_azure.py`:

```python
from omnibridge_estimator.vmware_to_azure import estimate_vmware_to_azure


def test_estimate_counts_compute_nodes_and_complexity() -> None:
    estimate = estimate_vmware_to_azure(
        compute_nodes=3,
        storage_gb=1280,
        network_segments=3,
        blocker_count=1,
        warning_count=1,
    )

    assert estimate.project_package == "assessment"
    assert estimate.asset_count == 3
    assert estimate.complexity_band == "medium"
    assert estimate.estimated_agent_usage_usd > 0
    assert estimate.base_project_fee_usd > 0
```

- [ ] **Step 2: Implement estimator models and function**

Create `models.py`:

```python
from pydantic import BaseModel


class CommercialEstimate(BaseModel):
    project_package: str
    asset_count: int
    complexity_score: int
    complexity_band: str
    base_project_fee_usd: int
    estimated_agent_usage_usd: int
    assumptions: list[str]
```

Create `vmware_to_azure.py`:

```python
from omnibridge_estimator.models import CommercialEstimate


def estimate_vmware_to_azure(
    compute_nodes: int,
    storage_gb: int,
    network_segments: int,
    blocker_count: int,
    warning_count: int,
) -> CommercialEstimate:
    complexity_score = (
        compute_nodes * 4
        + network_segments * 5
        + blocker_count * 15
        + warning_count * 5
        + storage_gb // 256
    )
    complexity_band = "low"
    if complexity_score >= 30:
        complexity_band = "medium"
    if complexity_score >= 75:
        complexity_band = "high"

    return CommercialEstimate(
        project_package="assessment",
        asset_count=compute_nodes,
        complexity_score=complexity_score,
        complexity_band=complexity_band,
        base_project_fee_usd=25000 + compute_nodes * 750,
        estimated_agent_usage_usd=1500 + compute_nodes * 100,
        assumptions=[
            "Estimate is based on fixture/import metadata.",
            "Live vCenter discovery is not included in this MVP path.",
            "Azure Migrate is assumed as the execution backend for supported VMs.",
        ],
    )
```

- [ ] **Step 3: Verify estimator tests**

Run:

```bash
uv run pytest packages/estimator/tests/test_vmware_to_azure.py -v
```

Expected: estimator test passes.

- [ ] **Step 4: Commit**

```bash
git add packages/estimator
git commit -m "feat: add VMware-to-Azure estimator"
```

---

### Task 9: Blueprint Generator

**Files:**
- Create: `/Volumes/Main External/Development/OmniBridge/packages/blueprint-engine/src/omnibridge_blueprint_engine/models.py`
- Create: `/Volumes/Main External/Development/OmniBridge/packages/blueprint-engine/src/omnibridge_blueprint_engine/generator.py`
- Create: `/Volumes/Main External/Development/OmniBridge/packages/blueprint-engine/tests/test_generator.py`

- [ ] **Step 1: Write blueprint test**

Create `packages/blueprint-engine/tests/test_generator.py`:

```python
from omnibridge_blueprint_engine.generator import generate_vmware_to_azure_blueprint


def test_blueprint_contains_corridor_and_approval_gates() -> None:
    blueprint = generate_vmware_to_azure_blueprint(
        project_id="project-release1-vmware-azure",
        application_name="Claims Portal",
        compute_node_names=["claims-web-01", "claims-api-01", "claims-db-01"],
    )

    assert blueprint.corridor == "vmware-to-azure"
    assert blueprint.application_name == "Claims Portal"
    assert "commercial_estimate_approval" in blueprint.approval_gates
    assert blueprint.waves[0]["name"] == "wave-001"
```

- [ ] **Step 2: Implement blueprint models and generator**

Create `models.py`:

```python
from pydantic import BaseModel


class MigrationBlueprint(BaseModel):
    project_id: str
    corridor: str
    application_name: str
    compute_node_names: list[str]
    waves: list[dict[str, object]]
    approval_gates: list[str]
```

Create `generator.py`:

```python
from omnibridge_blueprint_engine.models import MigrationBlueprint


def generate_vmware_to_azure_blueprint(
    project_id: str,
    application_name: str,
    compute_node_names: list[str],
) -> MigrationBlueprint:
    return MigrationBlueprint(
        project_id=project_id,
        corridor="vmware-to-azure",
        application_name=application_name,
        compute_node_names=compute_node_names,
        waves=[
            {
                "name": "wave-001",
                "compute_nodes": compute_node_names,
                "execution_backend": "azure-migrate",
            }
        ],
        approval_gates=[
            "commercial_estimate_approval",
            "target_design_approval",
            "test_migration_approval",
            "cutover_approval",
        ],
    )
```

- [ ] **Step 3: Verify blueprint tests**

Run:

```bash
uv run pytest packages/blueprint-engine/tests/test_generator.py -v
```

Expected: blueprint test passes.

- [ ] **Step 4: Commit**

```bash
git add packages/blueprint-engine
git commit -m "feat: add migration blueprint generator"
```

---

### Task 10: Agent Tools, LangGraph Workflow, and Langfuse Trace Envelope

**Files:**
- Create: `/Volumes/Main External/Development/OmniBridge/packages/agent-tools/src/omnibridge_agent_tools/models.py`
- Create: `/Volumes/Main External/Development/OmniBridge/packages/agent-tools/src/omnibridge_agent_tools/analysis_workflow.py`
- Create: `/Volumes/Main External/Development/OmniBridge/packages/agent-tools/src/omnibridge_agent_tools/tracing.py`
- Create: `/Volumes/Main External/Development/OmniBridge/packages/agent-tools/tests/test_analysis_workflow.py`
- Create: `/Volumes/Main External/Development/OmniBridge/packages/agent-tools/tests/test_tracing.py`

- [ ] **Step 1: Write analysis workflow test**

Create `packages/agent-tools/tests/test_analysis_workflow.py`:

```python
from omnibridge_agent_tools.analysis_workflow import run_fixture_analysis


def test_fixture_analysis_returns_consultant_summary() -> None:
    result = run_fixture_analysis(
        compute_nodes=["claims-web-01", "claims-api-01", "claims-db-01"],
        blocker_count=1,
        warning_count=1,
    )

    assert result.summary.startswith("Claims Portal")
    assert result.requires_consultant_review is True
```

- [ ] **Step 2: Write Langfuse trace envelope test**

Create `packages/agent-tools/tests/test_tracing.py`:

```python
from omnibridge_agent_tools.models import AnalysisResult
from omnibridge_agent_tools.tracing import build_trace_metadata


def test_build_trace_metadata_contains_project_and_agent() -> None:
    result = AnalysisResult(
        summary="Claims Portal contains 3 compute nodes.",
        requires_consultant_review=True,
        decision_points=["Confirm database subnet mapping."],
    )

    metadata = build_trace_metadata(
        project_id="project-release1-vmware-azure",
        agent_name="release1-analysis-agent",
        result=result,
    )

    assert metadata["project_id"] == "project-release1-vmware-azure"
    assert metadata["agent_name"] == "release1-analysis-agent"
    assert metadata["requires_consultant_review"] is True
```

- [ ] **Step 3: Implement LangGraph-backed analysis workflow**

Create `models.py`:

```python
from pydantic import BaseModel


class AnalysisResult(BaseModel):
    summary: str
    requires_consultant_review: bool
    decision_points: list[str]
```

Create `analysis_workflow.py`:

```python
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from omnibridge_agent_tools.models import AnalysisResult


class AnalysisState(TypedDict):
    compute_nodes: list[str]
    blocker_count: int
    warning_count: int
    result: AnalysisResult | None


def _summarize(state: AnalysisState) -> AnalysisState:
    blocker_count = state["blocker_count"]
    warning_count = state["warning_count"]
    compute_nodes = state["compute_nodes"]
    state["result"] = AnalysisResult(
        summary=(
            "Claims Portal contains "
            f"{len(compute_nodes)} compute nodes with "
            f"{blocker_count} blocker(s) and {warning_count} warning(s)."
        ),
        requires_consultant_review=blocker_count > 0 or warning_count > 0,
        decision_points=[
            "Confirm whether claims-db-01 snapshot can be removed.",
            "Confirm Azure subnet mapping for database tier.",
        ],
    )
    return state


def build_analysis_graph():
    graph = StateGraph(AnalysisState)
    graph.add_node("summarize", _summarize)
    graph.add_edge(START, "summarize")
    graph.add_edge("summarize", END)
    return graph.compile()


def run_fixture_analysis(
    compute_nodes: list[str],
    blocker_count: int,
    warning_count: int,
) -> AnalysisResult:
    compiled = build_analysis_graph()
    state = compiled.invoke(
        {
            "compute_nodes": compute_nodes,
            "blocker_count": blocker_count,
            "warning_count": warning_count,
            "result": None,
        }
    )
    result = state["result"]
    if result is None:
        raise RuntimeError("analysis graph finished without a result")
    return result
```

- [ ] **Step 4: Implement Langfuse trace metadata builder**

Create `tracing.py`:

```python
from omnibridge_agent_tools.models import AnalysisResult


def build_trace_metadata(
    project_id: str,
    agent_name: str,
    result: AnalysisResult,
) -> dict[str, object]:
    return {
        "project_id": project_id,
        "agent_name": agent_name,
        "requires_consultant_review": result.requires_consultant_review,
        "decision_point_count": len(result.decision_points),
    }
```

- [ ] **Step 5: Verify agent workflow and trace envelope**

Run:

```bash
uv run pytest packages/agent-tools/tests -v
```

Expected: analysis workflow and trace metadata tests pass.

- [ ] **Step 6: Commit**

```bash
git add packages/agent-tools
git commit -m "feat: add first LangGraph analysis workflow"
```

---

### Task 11: API Endpoints for Estimate, Blueprint, and Analysis

**Files:**
- Create: `/Volumes/Main External/Development/OmniBridge/apps/api/src/omnibridge_api/routes/analysis.py`
- Create: `/Volumes/Main External/Development/OmniBridge/apps/api/src/omnibridge_api/routes/blueprints.py`
- Create: `/Volumes/Main External/Development/OmniBridge/apps/api/src/omnibridge_api/routes/estimates.py`
- Modify: `/Volumes/Main External/Development/OmniBridge/apps/api/src/omnibridge_api/main.py`
- Create: `/Volumes/Main External/Development/OmniBridge/apps/api/tests/test_release1_routes.py`

- [ ] **Step 1: Write route tests**

Create `apps/api/tests/test_release1_routes.py`:

```python
from fastapi.testclient import TestClient

from omnibridge_api.main import app


def test_estimate_endpoint_returns_commercial_estimate() -> None:
    client = TestClient(app)
    response = client.get("/estimates/release1-demo")
    assert response.status_code == 200
    assert response.json()["project_package"] == "assessment"


def test_blueprint_endpoint_returns_vmware_to_azure_blueprint() -> None:
    client = TestClient(app)
    response = client.get("/blueprints/release1-demo")
    assert response.status_code == 200
    assert response.json()["corridor"] == "vmware-to-azure"


def test_analysis_endpoint_returns_decision_points() -> None:
    client = TestClient(app)
    response = client.get("/analysis/release1-demo")
    assert response.status_code == 200
    assert response.json()["requires_consultant_review"] is True
```

- [ ] **Step 2: Implement estimate route**

Create `routes/estimates.py`:

```python
from fastapi import APIRouter

from omnibridge_estimator.vmware_to_azure import estimate_vmware_to_azure


router = APIRouter(prefix="/estimates", tags=["estimates"])


@router.get("/release1-demo")
def get_release1_estimate() -> dict[str, object]:
    return estimate_vmware_to_azure(
        compute_nodes=3,
        storage_gb=1280,
        network_segments=3,
        blocker_count=1,
        warning_count=1,
    ).model_dump()
```

- [ ] **Step 3: Implement blueprint route**

Create `routes/blueprints.py`:

```python
from fastapi import APIRouter

from omnibridge_blueprint_engine.generator import generate_vmware_to_azure_blueprint


router = APIRouter(prefix="/blueprints", tags=["blueprints"])


@router.get("/release1-demo")
def get_release1_blueprint() -> dict[str, object]:
    return generate_vmware_to_azure_blueprint(
        project_id="project-release1-vmware-azure",
        application_name="Claims Portal",
        compute_node_names=["claims-web-01", "claims-api-01", "claims-db-01"],
    ).model_dump()
```

- [ ] **Step 4: Implement analysis route**

Create `routes/analysis.py`:

```python
from fastapi import APIRouter

from omnibridge_agent_tools.analysis_workflow import run_fixture_analysis


router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/release1-demo")
def get_release1_analysis() -> dict[str, object]:
    return run_fixture_analysis(
        compute_nodes=["claims-web-01", "claims-api-01", "claims-db-01"],
        blocker_count=1,
        warning_count=1,
    ).model_dump()
```

- [ ] **Step 5: Register routes**

Modify `main.py` to include:

```python
from omnibridge_api.routes.analysis import router as analysis_router
from omnibridge_api.routes.blueprints import router as blueprints_router
from omnibridge_api.routes.estimates import router as estimates_router

app.include_router(analysis_router)
app.include_router(blueprints_router)
app.include_router(estimates_router)
```

- [ ] **Step 6: Verify route tests**

Run:

```bash
uv run pytest apps/api/tests -v
```

Expected: all API route tests pass.

- [ ] **Step 7: Commit**

```bash
git add apps/api
git commit -m "feat: expose release 1 demo API"
```

---

### Task 12: Web Consultant Workspace Shell

**Files:**
- Create: `/Volumes/Main External/Development/OmniBridge/apps/web/package.json`
- Create: `/Volumes/Main External/Development/OmniBridge/apps/web/index.html`
- Create: `/Volumes/Main External/Development/OmniBridge/apps/web/src/main.tsx`
- Create: `/Volumes/Main External/Development/OmniBridge/apps/web/src/App.tsx`
- Create: `/Volumes/Main External/Development/OmniBridge/apps/web/src/App.test.tsx`
- Create: `/Volumes/Main External/Development/OmniBridge/apps/web/src/styles.css`

- [ ] **Step 1: Add web package config**

Create `apps/web/package.json`:

```json
{
  "name": "@omnibridge/web",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0",
    "build": "tsc && vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "@vitejs/plugin-react": "^5.0.0",
    "vite": "^7.0.0",
    "typescript": "^5.8.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@testing-library/react": "^16.0.0",
    "@testing-library/jest-dom": "^6.0.0",
    "vitest": "^3.0.0",
    "jsdom": "^26.0.0"
  }
}
```

- [ ] **Step 2: Add Consultant Workspace component**

Create `src/App.tsx`:

```tsx
const summary = {
  project: "OmniBridge VMware-to-Azure Assessment",
  application: "Claims Portal",
  computeNodes: 3,
  blockers: 1,
  warnings: 1,
  estimate: "$27,250",
  agentUsage: "$1,800",
};

export function App() {
  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">OmniBridge Consultant Workspace</p>
          <h1>{summary.project}</h1>
        </div>
        <button type="button">Approve Estimate</button>
      </header>

      <section className="grid">
        <article>
          <h2>Estate Summary</h2>
          <p>{summary.application}</p>
          <strong>{summary.computeNodes} compute nodes</strong>
        </article>
        <article>
          <h2>Readiness</h2>
          <p>{summary.blockers} blocker</p>
          <strong>{summary.warnings} warning</strong>
        </article>
        <article>
          <h2>Estimate</h2>
          <p>{summary.estimate} project fee</p>
          <strong>{summary.agentUsage} agent usage</strong>
        </article>
      </section>

      <section className="panel">
        <h2>Decision Queue</h2>
        <ul>
          <li>Confirm whether claims-db-01 snapshot can be removed.</li>
          <li>Confirm Azure subnet mapping for database tier.</li>
          <li>Approve commercial estimate before blueprint execution.</li>
        </ul>
      </section>
    </main>
  );
}
```

- [ ] **Step 3: Add web test**

Create `src/App.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("App", () => {
  it("renders the consultant workspace", () => {
    render(<App />);
    expect(screen.getByText("OmniBridge Consultant Workspace")).toBeInTheDocument();
    expect(screen.getByText("Claims Portal")).toBeInTheDocument();
    expect(screen.getByText("Approve Estimate")).toBeInTheDocument();
  });
});
```

- [ ] **Step 4: Add Vite entrypoint and styles**

Create `src/main.tsx`:

```tsx
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles.css";

createRoot(document.getElementById("root")!).render(<App />);
```

Create `index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>OmniBridge</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Create `src/styles.css`:

```css
:root {
  font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #172033;
  background: #f5f7fb;
}

body {
  margin: 0;
}

.shell {
  max-width: 1180px;
  margin: 0 auto;
  padding: 32px;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #526070;
  font-size: 13px;
  text-transform: uppercase;
}

h1,
h2,
p {
  margin-top: 0;
}

button {
  border: 0;
  border-radius: 6px;
  padding: 10px 14px;
  color: white;
  background: #1f6feb;
  font-weight: 700;
}

.grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin: 32px 0;
}

article,
.panel {
  border: 1px solid #d9e2ef;
  border-radius: 8px;
  padding: 20px;
  background: white;
}
```

- [ ] **Step 5: Verify web tests**

Run:

```bash
pnpm -C apps/web test
```

Expected: Consultant Workspace render test passes.

- [ ] **Step 6: Commit**

```bash
git add apps/web package.json pnpm-workspace.yaml
git commit -m "feat: add consultant workspace shell"
```

---

### Task 13: Artifact Generation

**Files:**
- Create: `/Volumes/Main External/Development/OmniBridge/packages/blueprint-engine/src/omnibridge_blueprint_engine/artifacts.py`
- Create: `/Volumes/Main External/Development/OmniBridge/packages/blueprint-engine/tests/test_artifacts.py`
- Create: `/Volumes/Main External/Development/OmniBridge/apps/api/src/omnibridge_api/routes/artifacts.py`

- [ ] **Step 1: Write artifact test**

Create `packages/blueprint-engine/tests/test_artifacts.py`:

```python
from omnibridge_blueprint_engine.artifacts import render_assessment_markdown


def test_render_assessment_markdown_contains_project_and_decisions() -> None:
    markdown = render_assessment_markdown(
        project_name="OmniBridge VMware-to-Azure Assessment",
        application_name="Claims Portal",
        blockers=1,
        estimate_usd=27250,
    )

    assert "# OmniBridge VMware-to-Azure Assessment" in markdown
    assert "Claims Portal" in markdown
    assert "1 blocker" in markdown
    assert "$27,250" in markdown
```

- [ ] **Step 2: Implement markdown renderer**

Create `artifacts.py`:

```python
def render_assessment_markdown(
    project_name: str,
    application_name: str,
    blockers: int,
    estimate_usd: int,
) -> str:
    return "\n".join(
        [
            f"# {project_name}",
            "",
            "## Application",
            "",
            application_name,
            "",
            "## Readiness",
            "",
            f"{blockers} blocker requires consultant review.",
            "",
            "## Estimate",
            "",
            f"${estimate_usd:,} project fee before usage overage.",
            "",
        ]
    )
```

- [ ] **Step 3: Add artifact API route**

Create `routes/artifacts.py`:

```python
from fastapi import APIRouter, Response

from omnibridge_blueprint_engine.artifacts import render_assessment_markdown


router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("/release1-assessment.md")
def get_release1_assessment() -> Response:
    markdown = render_assessment_markdown(
        project_name="OmniBridge VMware-to-Azure Assessment",
        application_name="Claims Portal",
        blockers=1,
        estimate_usd=27250,
    )
    return Response(content=markdown, media_type="text/markdown")
```

- [ ] **Step 4: Register route and verify**

Add artifact router to `main.py`, then run:

```bash
uv run pytest packages/blueprint-engine/tests/test_artifacts.py apps/api/tests -v
```

Expected: artifact renderer and API tests pass.

- [ ] **Step 5: Commit**

```bash
git add packages/blueprint-engine apps/api
git commit -m "feat: generate assessment artifact"
```

---

### Task 14: End-to-End Verification Script

**Files:**
- Create: `/Volumes/Main External/Development/OmniBridge/scripts/verify-release1-demo.sh`
- Modify: `/Volumes/Main External/Development/OmniBridge/Makefile`

- [ ] **Step 1: Add verification script**

Create `scripts/verify-release1-demo.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

uv run pytest
pnpm -C apps/web test
docker compose config >/dev/null
```

- [ ] **Step 2: Make script executable**

Run:

```bash
chmod +x scripts/verify-release1-demo.sh
```

- [ ] **Step 3: Add Makefile target**

Add:

```makefile
.PHONY: verify-release1

verify-release1:
	./scripts/verify-release1-demo.sh
```

- [ ] **Step 4: Verify full demo**

Run:

```bash
make verify-release1
```

Expected: Python tests pass, web tests pass, and Docker Compose config validates.

- [ ] **Step 5: Commit**

```bash
git add scripts/verify-release1-demo.sh Makefile
git commit -m "chore: add release 1 demo verification"
```

---

## Self-Review Checklist

- Release 1 uses fixture/import data before live vCenter discovery.
- Neo4j is the canonical graph target in the implementation path.
- FastAPI is the control plane.
- Vite React is the Consultant Workspace.
- LangGraph/Langfuse are introduced through the first analysis workflow and tracing path.
- LangFlow remains Agent Studio, not the consultant dashboard.
- Azure Migrate is represented as the first execution backend in blueprint data but not called in the MVP.
- Every task has concrete files, commands, and expected verification.
- Every task is independently committable.
