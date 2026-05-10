# OmniBridge Architecture

## 1. Architecture Thesis

OmniBridge is a graph-native, agent-assisted migration factory.

The product should not be built as a pile of migration scripts. It should be built as a platform that turns source environments into a canonical knowledge graph, lets specialized agents reason over that graph, generates priced migration blueprints, and executes approved workflows through deterministic integrations.

Core principles:

- Neo4j is the canonical infrastructure and migration knowledge graph.
- Agents reason over structured tools, GraphRAG, and typed workflow state.
- Consultants use the OmniBridge Consultant Workspace, not raw agent-builder tools.
- LangFlow is the Agent Studio for engineering and agent capability design.
- LangGraph is the production agent workflow runtime.
- Langfuse is the observability, trace, prompt, eval, and cost layer.
- Existing execution platforms should be used wherever they fit.
- Azure Migrate is the first execution backend for VMware-to-Azure.
- Humans approve risky or commercially material decisions.
- Deterministic services execute state changes.

## 2. System Overview

```text
OmniBridge Consultant Workspace
   -> API / Control Plane
      -> Neo4j Canonical Graph and GraphRAG
      -> PostgreSQL Transaction Ledger
      -> Object Storage Artifact Store
      -> LangGraph Agent Runtime
      -> LangFlow Agent Studio
      -> Langfuse Observability
      -> Workflow and Approval Engine
      -> Corridor SDK
      -> Connector SDK
      -> Backend Adapters
         -> Azure Migrate
         -> Azure Resource Manager
         -> Terraform / IaC engines
         -> future third-party systems
      -> On-Prem Appliance
         -> vCenter connector
         -> local collection
         -> credential boundary
```

The high-level data path:

```text
Source Estate
   -> Connector
   -> Raw Import Snapshot
   -> Canonical Graph Ingestion
   -> Neo4j Estate Graph
   -> GraphRAG and Agent Analysis
   -> Readiness Findings
   -> Cost and Effort Estimate
   -> Migration Blueprint
   -> Customer Approval
   -> Execution Backend
   -> Validation Evidence
```

## 3. Repository Architecture

The repository should remain a monorepo with platform and corridor boundaries.

```text
apps/
  web/
  api/
  appliance/

packages/
  canonical-graph/
  corridor-sdk/
  connector-sdk/
  workflow-engine/
  estimator/
  blueprint-engine/
  rules-engine/
  agent-tools/
  artifact-store/
  policy-engine/

connectors/
  vmware-vcenter/
  azure-arm/
  azure-migrate/

corridors/
  vmware-to-azure/

docs/
  PRODUCT_SPEC.md
  ARCHITECTURE.md
  CORRIDOR_CONTRACT.md
```

Ownership rule:

```text
Platform packages own reusable factory capabilities.
Connectors own source or target API access.
Corridors own source-to-target migration knowledge.
Apps own user-facing and deployable surfaces.
```

## 4. Primary Technology Choices

### Frontend

Use TypeScript and React for the Consultant Workspace.

Start with Vite React unless server-rendered routes become necessary. The first product is an operational dashboard and workflow tool, not a public marketing app, so fast local development and clear component boundaries matter more than SSR.

Responsibilities:

- project workspace
- estate graph explorer
- consultant dashboard
- estimate and SOW review
- blueprint review
- approval queue
- migration wave dashboard
- validation evidence viewer
- embedded Agent Studio entry points
- observability summaries

### API / Control Plane

Use Python FastAPI for the control plane.

Python fits the agent, GraphRAG, data-processing, and cloud SDK ecosystem. FastAPI gives typed request/response models and enough structure for the first control-plane API without forcing a heavy framework.

Responsibilities:

- project APIs
- graph query APIs
- import APIs
- corridor APIs
- estimate APIs
- blueprint APIs
- approval APIs
- artifact APIs
- agent run APIs
- backend adapter APIs
- audit/event APIs

### Canonical Graph

Use Neo4j as the primary graph and knowledge substrate.

Neo4j is not an optional read projection in this product. The canonical graph is the product's core reasoning layer, and agents should use it through typed tools and GraphRAG retrieval.

### Transaction Ledger

Use PostgreSQL for transactional control-plane records.

PostgreSQL should store records that are not naturally graph-primary:

- users
- organizations
- project membership
- auth-related records
- approval records
- workflow run metadata
- billing records
- agent usage summaries
- artifact metadata
- audit event envelopes

PostgreSQL should not become a second canonical graph. The source of truth for estate topology, infrastructure relationships, migration knowledge, and dependency reasoning is Neo4j.

### Artifact Store

Use object storage for generated and imported artifacts.

Local development can use filesystem storage or MinIO. Production should use Azure Blob Storage or an S3-compatible object store.

Artifacts:

- raw inventory snapshots
- generated reports
- SOW packets
- migration blueprints
- IaC bundles
- runbooks
- validation evidence
- exported graph snapshots
- customer closeout packets

## 5. Neo4j Graph Architecture

Neo4j should contain three connected graph layers.

```text
Estate Graph
   + Migration Knowledge Graph
   + Project Decision Graph
   = OmniBridge Canonical Graph
```

### Estate Graph

Represents discovered source and target environment facts.

Example node labels:

- `Project`
- `SourceConnector`
- `TargetConnector`
- `ComputeNode`
- `StorageVolume`
- `NetworkInterface`
- `NetworkSegment`
- `Datastore`
- `Cluster`
- `Host`
- `Application`
- `ServiceEndpoint`
- `Environment`
- `Owner`
- `CostCenter`
- `SecurityPolicy`

Example relationships:

- `RUNS_ON`
- `BELONGS_TO`
- `USES_DATASTORE`
- `HAS_VOLUME`
- `HAS_INTERFACE`
- `CONNECTED_TO`
- `EXPOSES_ENDPOINT`
- `DEPENDS_ON`
- `PART_OF_APPLICATION`
- `OWNED_BY`
- `HAS_COST_CENTER`

### Migration Knowledge Graph

Represents reusable migration expertise.

Example node labels:

- `Corridor`
- `MigrationPattern`
- `ReadinessRule`
- `ValidationRule`
- `RemediationPlaybook`
- `TargetDesignPattern`
- `CloudService`
- `AzureSkuFamily`
- `RiskFactor`
- `DocumentationChunk`
- `PolicyControl`

Example relationships:

- `APPLIES_TO`
- `BLOCKS`
- `REMEDIATED_BY`
- `PROJECTS_TO`
- `REQUIRES_APPROVAL`
- `VALIDATED_BY`
- `SUPPORTED_BY_BACKEND`
- `REFERENCES_DOC`

### Project Decision Graph

Represents project-specific decisions and commercial state that agents need to reason over.

Example node labels:

- `CommercialEstimate`
- `Assumption`
- `Unknown`
- `Approval`
- `Decision`
- `Recommendation`
- `MigrationBlueprint`
- `MigrationWave`
- `GeneratedArtifact`
- `ValidationEvidence`
- `ChangeOrder`

Example relationships:

- `PRICES`
- `ASSUMES`
- `REQUIRES_DECISION`
- `APPROVES`
- `REJECTS`
- `GENERATED_FROM`
- `SUPERSEDES`
- `TRIGGERS_CHANGE_ORDER`
- `VALIDATES`

### Graph Identity

Every graph node should carry:

- `id`
- `project_id`
- `tenant_id`
- `source_connector_id`
- `source_platform`
- `source_object_type`
- `source_object_id`
- `canonical_type`
- `name`
- `normalized_name`
- `confidence`
- `created_at`
- `updated_at`
- `graph_version`
- `provenance`

Every relationship should carry:

- `id`
- `project_id`
- `tenant_id`
- `confidence`
- `evidence`
- `source`
- `created_at`
- `updated_at`
- `graph_version`
- `confirmed_by_user`

### Graph Versioning

The graph must support version-aware reasoning.

Required capabilities:

- compare discovery run to previous graph state
- identify added, changed, and removed nodes
- identify changed dependencies
- mark estimates and blueprints stale when graph changes matter
- reproduce approved blueprints from the graph version that generated them
- explain why a change order was triggered

### Repository Contract

The canonical graph package owns the Neo4j persistence contract.

Current repository responsibilities:

- bootstrap Neo4j constraints and project-scoped indexes
- upsert canonical graph nodes
- upsert canonical graph relationships after nodes exist
- ingest a complete mapped graph as nodes first, relationships second
- return project topology summaries for agent tools and consultant surfaces

The API import path can run in two modes:

- import and count a fixture without persistence
- import, bootstrap schema, and persist the graph into Neo4j when `persist_to_neo4j` is requested

Local Neo4j configuration uses:

```text
OMNIBRIDGE_NEO4J_URI
OMNIBRIDGE_NEO4J_USER
OMNIBRIDGE_NEO4J_PASSWORD
```

This gives corridor discovery a deterministic path into the canonical graph before GraphRAG and production agents query it.

## 6. GraphRAG Architecture

GraphRAG is a core agent capability, not a side feature.

Agents should retrieve from:

- graph traversals
- Cypher queries
- vector search over documentation and generated artifacts
- hybrid graph plus vector retrieval
- project-specific corrections
- corridor-specific migration knowledge

Retrieval pattern:

```text
User or workflow question
   -> classify intent
   -> choose typed graph tool
   -> retrieve graph neighborhood
   -> retrieve relevant docs/rules/playbooks
   -> assemble grounded context
   -> agent produces answer/recommendation
   -> answer cites graph evidence and assumptions
```

Agent responses should distinguish:

- observed facts
- inferred relationships
- user-confirmed decisions
- rule-based blockers
- AI recommendations
- unknowns
- assumptions

No production agent should receive unrestricted arbitrary Cypher write access.

## 7. Agent Architecture

### Roles

Core production agents:

- Discovery Interpretation Agent
- Topology Agent
- Application Grouping Agent
- Dependency Agent
- Target Architecture Agent
- Readiness Agent
- Cost and Effort Estimation Agent
- Blueprint Agent
- Customer Deliverables Agent
- Validation Agent
- Remediation Agent
- Change Order Agent

### Runtime

Use LangGraph for production agent workflows.

Production agent workflows need:

- durable state
- resumability
- explicit workflow nodes
- human approval interrupts
- tool boundaries
- deterministic transition points
- traceability

LangGraph owns production orchestration of agent steps. It does not replace the deterministic workflow engine for migration execution.

### Agent Studio

Use LangFlow as the embedded Agent Studio.

LangFlow is for engineering and advanced operator workflows:

- visualize agent flows
- design agent capabilities
- inspect tool wiring
- test flows against fixture estates
- prototype retrieval patterns
- review agent behavior
- prepare candidate agent versions

LangFlow is not the primary consultant dashboard. Consultants should use OmniBridge surfaces that translate agent output into migration decisions, approvals, and customer deliverables.

### Observability

Use Langfuse for agent observability.

Langfuse should track:

- traces
- sessions
- prompt versions
- model usage
- token and cost data
- tool calls
- latency
- errors
- eval scores
- production regressions

The Consultant Workspace should show product-level summaries of Langfuse data. Engineering users can drill into Langfuse-level traces when debugging.

### Agent Promotion Lifecycle

Agent changes should have a controlled path:

```text
Draft in LangFlow
   -> test against fixture estates
   -> run eval suite
   -> inspect Langfuse traces
   -> approve candidate version
   -> publish to Agent Registry
   -> execute through LangGraph
   -> monitor production traces
   -> feed failures back into LangFlow iteration
```

Production migration behavior should only use approved agent versions.

## 8. Consultant Workspace

The Consultant Workspace is the main product UI.

It should expose:

- customer projects
- project lifecycle state
- discovery status
- estate graph views
- application groups
- dependency findings
- readiness findings
- risk register
- estimates and SOWs
- assumptions and unknowns
- migration blueprints
- approval queue
- migration wave dashboard
- validation results
- change-order alerts
- customer deliverable generation

The Consultant Workspace should be decision-oriented.

Example actions:

- approve an app grouping
- reject a dependency inference
- request customer clarification
- approve network mapping
- approve target design
- approve commercial estimate
- generate SOW package
- move a wave into test-ready state
- approve cutover
- generate validation packet

The interface should hide unnecessary agent internals from normal consultant workflows.

## 9. Deterministic Workflow and Approvals

Agent workflows and deterministic execution workflows should be separate.

```text
Agent workflow:
  analyze, explain, recommend, draft

Execution workflow:
  validate approval, call backend, mutate source/target, record evidence
```

Approval gates:

- discovery authorization
- commercial estimate approval
- target design approval
- blueprint approval
- Azure resource creation
- test migration approval
- source snapshot approval
- source shutdown approval
- cutover approval
- decommission approval
- change-order approval

Agents may recommend actions, but deterministic services must enforce approval requirements before execution.

## 10. Integration-First Backend Strategy

OmniBridge should prefer existing platforms over rebuilding infrastructure machinery.

Before implementing a sub-tool internally, ask:

1. Does a mature product already do this safely?
2. Can OmniBridge integrate with it through an adapter?
3. Can the adapter expose enough state for graph reasoning, approvals, and validation?
4. Does owning this capability create product differentiation?

For VMware-to-Azure:

```text
Azure Migrate = preferred migration execution backend
Azure Resource Manager = target resource API
Terraform/Bicep = generated infrastructure artifact formats
ServiceNow/Jira/Azure DevOps = future change/task integrations
```

OmniBridge differentiates through graph intelligence, agent planning, estimation, blueprints, workflow control, validation evidence, and repeatable delivery. It should not rebuild Azure Migrate unless a corridor requires unsupported behavior.

## 11. Adapter Model

Adapters wrap existing services behind typed OmniBridge contracts.

Adapter categories:

- execution backend adapters
- cloud control-plane adapters
- ticketing/change adapters
- artifact adapters
- observability adapters
- agent design/runtime adapters
- identity/secret adapters

Initial adapters:

- `azure-migrate-adapter`
- `azure-arm-adapter`
- `neo4j-graphrag-adapter`
- `langgraph-runtime-adapter`
- `langflow-agent-studio-adapter`
- `langfuse-observability-adapter`
- `object-storage-adapter`

Adapter calls should be:

- typed
- permissioned
- audited
- idempotent where execution is involved
- trace-linked to project and workflow IDs

## 12. Security and Appliance Boundary

The on-prem appliance exists to make enterprise security workable.

The appliance should:

- run inside the customer environment
- connect outbound only
- keep customer credentials local or in a customer-approved vault
- collect source metadata
- redact sensitive data
- send approved metadata to the control plane
- perform approved local execution steps
- keep local logs

The SaaS control plane should:

- store normalized graph data
- run agent workflows on approved data
- manage approvals
- generate deliverables
- coordinate execution state
- integrate with cloud APIs

Data that should not be collected by default:

- guest file contents
- application secrets
- database row data
- private keys
- full packet captures
- customer source code

Any deeper collection should require explicit project approval.

## 13. Secrets

Secret storage should follow environment maturity.

Local development:

- `.env`
- Docker Compose secrets where practical

Pilot deployments:

- Azure Key Vault or HashiCorp Vault
- appliance-local credential store

Enterprise deployments:

- customer-managed vault integration
- tenant-specific encryption boundaries
- explicit credential access audit

Agents should never receive raw secrets in prompt context.

## 14. Event Model

OmniBridge should emit domain events from the start.

Initial event examples:

- `ProjectCreated`
- `DiscoveryAuthorized`
- `InventoryImported`
- `GraphIngested`
- `GraphChanged`
- `ApplicationGroupProposed`
- `ApplicationGroupApproved`
- `ReadinessAnalyzed`
- `EstimateGenerated`
- `EstimateApproved`
- `BlueprintGenerated`
- `BlueprintApproved`
- `ChangeOrderRequired`
- `AgentRunStarted`
- `AgentRunCompleted`
- `ValidationFailed`
- `ValidationPassed`

In v1, events can be stored through the API and replayed from the transaction ledger. Later, the implementation can move to NATS, Kafka, cloud queues, or another event bus if needed.

## 15. Evaluation Harness

Agent behavior must be testable.

Release 1 should include fixture-based evals:

- sample VMware estate
- expected canonical graph facts
- expected application grouping
- expected readiness findings
- expected estimate drivers
- expected blueprint sections
- expected customer decision points

Eval types:

- deterministic schema checks
- graph fact checks
- retrieval quality checks
- answer grounding checks
- estimate stability checks
- hallucination checks
- regression checks between agent versions

Langfuse should record eval results and traces, but OmniBridge should own the product-specific eval fixtures and pass/fail criteria.

## 16. Local Development Stack

Use Docker Compose for the local platform stack.

Base profile:

- Neo4j
- PostgreSQL
- object storage
- API
- web

Agent profile:

- LangGraph runtime service
- LangFlow
- Langfuse
- supporting Langfuse dependencies as required

Fixture profile:

- sample VMware inventory files
- graph ingestion job
- demo project seed

The first working vertical slice should run locally with:

```text
sample VMware inventory
   -> import API
   -> Neo4j graph ingestion
   -> GraphRAG-backed analysis
   -> application grouping
   -> readiness findings
   -> cost estimate
   -> migration blueprint
   -> consultant dashboard
```

## 17. Release 1 Architecture Scope

Release 1 should build the import-based assessment path before live vCenter discovery.

Build order:

1. repository scaffolding
2. Docker Compose base stack
3. Neo4j schema and graph constraints
4. VMware fixture format
5. fixture importer
6. canonical graph ingestion
7. graph query API
8. Consultant Workspace shell
9. estate graph and project dashboard
10. VMware-to-Azure corridor mappings
11. readiness rules
12. estimator
13. blueprint generator
14. LangGraph agent workflow for analysis
15. LangFlow Agent Studio integration
16. Langfuse tracing/evals integration
17. generated assessment/SOW artifact

Live vCenter discovery should come after the graph, estimator, blueprint, and dashboard flow prove useful against fixtures.

## 18. First Vertical Slice

The first demo should prove the product spine:

```text
Upload or seed sample VMware inventory
   -> create project
   -> ingest into Neo4j
   -> show estate graph
   -> run analysis agents
   -> propose application groups
   -> show readiness findings
   -> generate estimate
   -> generate migration blueprint
   -> show consultant approval queue
```

Definition of done:

- one command starts the local stack
- one fixture project can be seeded
- Neo4j contains the canonical graph
- API can query graph nodes and relationships
- web UI shows project, graph summary, findings, estimate, and blueprint
- agent run is traced in Langfuse
- agent workflow is represented in LangGraph
- LangFlow can be opened as Agent Studio for flow inspection or iteration
- generated artifacts are written to object storage or local artifact storage

## 19. Architecture References

- [Neo4j GraphRAG for Python](https://neo4j.com/docs/neo4j-graphrag-python/current/index.html)
- [Neo4j Documentation](https://neo4j.com/docs)
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph)
- [LangGraph durable execution](https://docs.langchain.com/oss/python/langgraph/durable-execution)
- [LangFlow documentation](https://docs.langflow.org/)
- [LangFlow agents](https://docs.langflow.org/agents)
- [Langfuse documentation](https://langfuse.com/docs/)
- [Azure Migrate REST API](https://learn.microsoft.com/en-us/rest/api/migrate/)
