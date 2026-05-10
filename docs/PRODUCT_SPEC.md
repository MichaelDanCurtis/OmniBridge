# OmniBridge Migration Factory Product Spec

## 1. Product Thesis

OmniBridge is an AI-assisted migration factory for moving enterprise technology estates from one operating environment to another. It starts with VMware-to-Azure, but the durable product is broader: a repeatable system that discovers source environments, converts them into a canonical technology graph, lets specialized agents reason over that graph, generates migration blueprints, estimates cost and effort, and executes approved workflows through deterministic engines.

The operating principle is:

> AI plans, explains, estimates, and proposes. Deterministic engines execute. Humans approve risky or ambiguous decisions.

The goal is not a one-click black box. The goal is to reduce the human team required for complex migration work from a large consulting bench to a handful of reviewers, approvers, and domain experts.

OmniBridge should make migrations feel like a factory:

1. Connect to the source environment.
2. Discover the estate.
3. Build a canonical graph.
4. Let agents classify, map, estimate, and design.
5. Generate a migration blueprint and commercial estimate.
6. Get customer approval.
7. Execute controlled migration workflows.
8. Validate the result and produce evidence.

## 2. Initial Wedge

The first product package is:

**VMware-to-Azure Migration Factory for MSPs, cloud consultants, and migration teams.**

This buyer runs repeat migrations and cares about repeatability, speed, cost clarity, client-facing deliverables, fewer senior engineers per project, and clean handoffs from assessment to execution.

The first release should help a team walk into a customer environment, connect to vCenter, discover the estate, produce a topology model, generate Azure target recommendations, estimate project scope and cost, create a migration blueprint, and prepare the customer for approval.

The first release should not try to replace every Azure Migrate or custom conversion capability. Azure Migrate should be treated as the default production execution backend where it fits. Custom conversion and replication engines can come later when there is a specific customer or product reason to own that complexity.

## 3. Long-Term Platform Vision

VMware-to-Azure is the first corridor, not the entire platform.

OmniBridge should eventually support many corridors:

- VMware to Azure
- VMware to AWS
- VMware to GCP
- AWS to Azure
- Azure to AWS
- GCP to Azure
- On-prem infrastructure to cloud-native infrastructure
- Domino, MLflow, or similar ML platforms to Azure ML or other target platforms
- Other specialized platform migrations where a source estate can be modeled, transformed, and validated

The system should be built around reusable primitives:

```text
Source Connector
   -> Canonical Technology Graph
   -> Agent Interpretation
   -> Target Projection
   -> Migration Blueprint
   -> Cost and Effort Estimate
   -> Approval Package
   -> Execution Workflow
   -> Validation Evidence
```

Every new corridor should reuse the same factory architecture and add only the corridor-specific pieces:

- source connector
- source-to-canonical mapper
- target adapter
- readiness rules
- execution backend
- validation checks
- pricing/effort model adjustments

## 4. Canonical Technology Graph

The core product asset is the canonical graph. This graph represents enterprise technology primitives independently from any one platform.

Most enterprise systems share primordial constructs. A VM in VMware, an Azure VM, an EC2 instance, a GCP Compute Engine instance, and a bare-metal server are all provider-specific expressions of a deeper primitive: a compute node. Linux and Windows are not separate product worlds; they are attributes of the compute node.

The graph should model these primitives as anchor points:

- `ComputeNode`
- `StorageVolume`
- `NetworkSegment`
- `NetworkInterface`
- `IdentityPrincipal`
- `SecurityPolicy`
- `Application`
- `ServiceEndpoint`
- `DataStore`
- `Runtime`
- `SecretReference`
- `Job`
- `Pipeline`
- `ModelArtifact`
- `Environment`
- `Owner`
- `CostCenter`
- `ComplianceControl`

Example:

```text
VMware VirtualMachine
   -> ComputeNode
      - cpu
      - memory
      - firmware
      - runtime_os
      - lifecycle_state
      - owner
      - environment
      - platform_specific.vmware_moid
```

```text
Azure Virtual Machine
   <- ComputeNode
      - cpu
      - memory
      - firmware
      - runtime_os
      - lifecycle_state
      - owner
      - environment
      - platform_specific.azure_resource_id
```

The canonical graph gives OmniBridge leverage. It lets the product reason about source estates before deciding how to project them into a target platform.

## 5. First Corridor: VMware to Azure

The first corridor turns VMware estates into Azure migration blueprints.

The system should discover:

- vCenter instances
- datacenters
- clusters
- hosts
- resource pools
- folders
- datastores
- standard switches
- distributed switches
- port groups
- vApps
- VMs
- disks
- disk controllers
- NICs
- snapshots
- guest OS metadata
- VMware Tools status
- tags
- custom attributes
- observed IP addresses
- dependency signals where available

The system should transform those objects into canonical graph primitives, then project them into an Azure target design:

- subscriptions
- resource groups
- regions
- VNets
- subnets
- NSGs
- route tables
- VM sizes
- managed disks
- availability zones or sets
- backup policies
- monitoring policies
- boot diagnostics
- tags
- identities

The first corridor should support Azure Migrate orchestration as the default production migration path. Custom VMDK-to-VHD conversion should be a later corridor capability unless required by a specific customer deal.

## 6. Product Suite

OmniBridge should feel like one suite with several tightly connected products:

1. **Discovery and Topology Mapper**
   Connects to the source environment, inventories assets, and builds the canonical graph.

2. **AI Application and Dependency Mapper**
   Uses names, folders, tags, networks, observed traffic, metadata, and user corrections to infer application groups and dependencies.

3. **Target Design Copilot**
   Recommends the target architecture for the selected migration corridor.

4. **Readiness and Risk Analyzer**
   Runs deterministic checks, flags blockers, scores risk, and explains remediation paths.

5. **Cost, Effort, and SOW Estimator**
   Estimates project cost, agent/token usage, execution effort, migration wave complexity, and risk-based contingencies before the customer approves the work.

6. **Migration Blueprint Generator**
   Produces the structured contract between source state, target design, approvals, execution, and validation.

7. **IaC and Runbook Generator**
   Produces Terraform, Bicep, ARM templates, runbooks, rollback plans, test plans, and change-ticket summaries.

8. **Migration Factory Dashboard**
   Tracks waves, approvals, test migrations, cutovers, validation, exceptions, and evidence.

9. **Validation and Remediation Assistant**
   Checks post-migration health and proposes fixes when validation fails.

## 7. Pre-Sales Assessment and SOW Workflow

Cost estimation should be a core workflow, not an afterthought.

OmniBridge should help a sales or delivery team enter a customer environment, run a scoped discovery, produce a concrete project estimate, and turn that estimate into a signed statement of work or approval package.

The pre-sales workflow:

```text
Connect discovery credentials
   -> inventory source estate
   -> build canonical graph
   -> classify applications and workloads
   -> estimate migration complexity
   -> estimate agent/token usage
   -> estimate delivery effort
   -> estimate infrastructure execution cost
   -> generate customer-facing assessment
   -> customer approves scope and commercial model
   -> approved estimate becomes part of the migration blueprint
```

The estimate should break down:

- discovered asset count
- in-scope asset count
- out-of-scope asset count
- application group count
- migration wave count
- expected blocker count
- network mapping complexity
- storage volume count and size
- high-risk workload count
- expected Azure Migrate orchestration effort
- expected custom handling effort
- expected agent/token usage
- expected human review hours
- required customer decision points
- assumptions
- exclusions
- confidence level

The signed estimate should become an auditable project object:

```yaml
kind: commercial.estimate
version: 1
project: customer-prod-vmware-to-azure
corridor: vmware-to-azure
scope:
  discovered_assets: 2841
  in_scope_compute_nodes: 420
  app_groups: 38
  planned_waves: 12
pricing:
  project_package: migration_factory
  base_project_fee: 125000
  included_agent_usage_usd: 15000
  agent_usage_overage: pass_through_plus_margin
  estimated_delivery_services: 60000
confidence:
  estimate_confidence: 0.78
  unknowns:
    - guest credential access not yet provided
    - dependency data partially observed
    - 19 source networks require customer mapping
approvals:
  customer_scope_approval: required
  commercial_approval: required
  change_control_required: true
```

This commercial estimate should be linked to the migration blueprint so that scope, price, assumptions, and delivery obligations do not drift silently during execution.

## 8. Commercial Model

OmniBridge should support project-based pricing with agent/token usage as a visible meter.

External packaging should not sound like raw token resale. Customers buy migration outcomes, assessments, blueprints, and controlled execution. Tokens are a cost and usage meter underneath that product.

Recommended packaging:

### Assessment Project

For customers who need a concrete migration plan before committing to full execution.

Includes:

- source environment discovery
- canonical graph
- topology and application grouping
- readiness report
- target design recommendations
- migration blueprint draft
- cost and effort estimate
- customer-facing SOW package
- baseline agent usage allowance

### Migration Factory Project

For customers ready to execute migrations.

Includes:

- everything in Assessment Project
- approved migration blueprints
- wave planning
- Azure Migrate orchestration where supported
- IaC and runbook generation
- validation evidence
- approval workflows
- exception management
- baseline agent usage allowance
- overage for heavy AI analysis or generation

### Partner / MSP Package

For repeat delivery organizations.

Includes:

- multi-customer project workspace
- reusable migration patterns
- branded client deliverables
- higher agent usage pool
- custom corridor support
- reusable estimate templates
- reporting across active projects

Pricing dimensions:

- project type
- migration corridor
- discovered asset count
- in-scope workload count
- application group count
- migration wave count
- source complexity
- target complexity
- custom connector or adapter requirements
- included agent/token allowance
- agent/token overage
- optional human delivery services

## 9. Agent Operating Model

The product should be agent-heavy but not agent-unbounded.

Agents should operate through typed tools and structured data. They should not execute arbitrary infrastructure mutations.

Core agents:

- Discovery Agent
- Topology Agent
- Application Grouping Agent
- Dependency Agent
- Target Architecture Agent
- Readiness Agent
- Cost and Effort Estimation Agent
- IaC Agent
- Runbook Agent
- Migration Planner Agent
- Validation Agent
- Remediation Agent
- Customer Deliverables Agent

Agents do:

- classify messy infrastructure
- infer likely application groups
- explain dependencies
- recommend target architecture
- identify blockers
- explain remediation
- estimate effort
- generate customer-facing documents
- generate IaC drafts
- generate runbooks
- summarize validation evidence
- suggest fixes

Humans do:

- approve source access
- approve scope and pricing
- resolve ambiguous business intent
- approve target architecture
- approve risky actions
- make cost, downtime, and security tradeoffs
- validate esoteric constructs
- approve production cutover
- approve decommissioning

Deterministic engines do:

- query provider APIs
- store graph objects
- run readiness rules
- enforce policies
- orchestrate workflow state
- create cloud resources after approval
- manage migration backend calls
- run validation checks
- write audit logs

## 10. Migration Blueprint

The migration blueprint is the main product artifact.

It is the contract between:

- source discovery
- canonical graph
- target design
- commercial estimate
- customer approvals
- execution workflow
- validation evidence
- rollback plan

Example:

```yaml
kind: migration.blueprint
version: 1
name: claims-portal-prod
corridor: vmware-to-azure
source:
  platform: vmware-vcenter
  vcenter: vcsa-prod-01
  app_group: Claims Portal
commercial:
  estimate_id: estimate-2026-05-claims-portal
  scope_approved: true
  agent_usage_metering: enabled
target:
  platform: azure
  region: westus2
  resource_group: rg-claims-prod
waves:
  - name: wave-001-db
    cutover_order: 1
    compute_nodes:
      - claims-db-01
  - name: wave-002-api
    cutover_order: 2
    compute_nodes:
      - claims-api-01
      - claims-api-02
  - name: wave-003-web
    cutover_order: 3
    compute_nodes:
      - claims-web-01
      - claims-web-02
network_mappings:
  dvpg-web-prod: snet-web
  dvpg-app-prod: snet-app
  dvpg-db-prod: snet-db
approvals:
  target_design: required
  test_migration: required
  source_shutdown: required
  cutover: required
  decommission: required
validation:
  checks:
    - vm_boot
    - azure_agent
    - disk_count
    - nic_ip
    - tcp_443
    - tcp_1433
    - app_health_url
```

The blueprint should be versioned. Agents can propose edits, but humans approve material changes.

## 11. Release 1 Scope

Release 1 should be called:

**OmniBridge VMware-to-Azure Design Copilot**

Release 1 should deliver:

- vCenter connection
- read-only estate discovery
- canonical graph creation
- VM, vApp, cluster, datastore, and network inventory
- topology drill-down
- application grouping suggestions
- Azure target design recommendations
- source-to-target network mapping assistant
- readiness and blocker analysis
- cost and effort estimator
- commercial assessment package
- migration blueprint generation
- Terraform or Bicep draft generation
- runbook generation
- Azure Migrate workflow mapping
- project dashboard
- audit trail for recommendations and approvals

Release 1 should explicitly not include:

- full custom VDDK replication
- powered-on custom CBT migration engine
- autonomous production cutover
- guest OS mutation without approved workflow
- automatic source VM deletion
- universal multi-cloud support
- generic ML platform migration support

## 12. Key User Workflows

### Workflow 1: Pre-Sales Assessment

1. MSP creates a customer project.
2. Customer deploys or approves the on-prem discovery appliance.
3. MSP enters read-only vCenter credentials.
4. OmniBridge discovers the VMware estate.
5. Agents classify workloads and infer application groups.
6. The estimator calculates cost, effort, risk, and token/agent usage.
7. OmniBridge generates a customer-facing assessment and SOW package.
8. Customer approves scope, assumptions, and commercial terms.
9. Approved estimate becomes part of the project blueprint.

### Workflow 2: Migration Design

1. User selects an application group, vApp, wave, or VM set.
2. Agents propose an Azure target design.
3. Readiness rules identify blockers.
4. Agents explain tradeoffs and remediation.
5. User approves the target design.
6. OmniBridge generates the migration blueprint.

### Workflow 3: Execution Preparation

1. OmniBridge generates IaC and runbooks.
2. System validates syntax, policy, and expected cost.
3. User links the blueprint to Azure Migrate where supported.
4. Migration wave enters test-ready state.

### Workflow 4: Test Migration and Validation

1. User approves test migration.
2. Workflow engine starts the migration backend.
3. System validates boot, agent status, NICs, disks, services, ports, and app endpoints.
4. Agents summarize results and suggest remediation.
5. User approves readiness for cutover or sends work back for remediation.

### Workflow 5: Cutover

1. User approves source shutdown and final sync.
2. Workflow engine runs the approved cutover process.
3. System validates target state.
4. Agents generate the cutover evidence report.
5. User approves completion or rollback.

## 13. UI Surfaces

Release 1 should include these core screens:

### Project Workspace

Shows customer, corridor, source environment, target environment, discovery status, estimate status, blueprint status, and active waves.

### Estate Map

Shows discovered infrastructure as a graph and hierarchy:

- datacenters
- clusters
- hosts
- datastores
- networks
- vApps
- VMs
- application groups
- blockers

### Application Group View

Shows inferred app topology, dependencies, confidence, user corrections, source metadata, target design, readiness status, and cost/effort contribution.

### Estimate and SOW View

Shows asset counts, complexity drivers, assumptions, exclusions, projected agent usage, delivery effort, project price, confidence, and customer approval status.

### Blueprint View

Shows source scope, target design, waves, network mappings, approvals, generated artifacts, execution state, and validation evidence.

### Migration Factory Dashboard

Shows waves, readiness, replication status, test migration status, validation status, cutover status, and exceptions.

### Assistant

Answers questions from the graph, blueprint, estimate, rules, and migration history.

Example questions:

- "Which VMs are driving the cost estimate?"
- "Why is this project priced as high complexity?"
- "Show every VM connected to VLAN 122."
- "Which workloads are blocked by snapshots?"
- "Generate an Azure design for the Claims Portal."
- "What assumptions are in the customer SOW?"
- "Which unknowns need customer decisions?"

## 14. Data Model Concepts

Core objects:

- `Project`
- `Customer`
- `Corridor`
- `SourceConnector`
- `TargetConnector`
- `GraphNode`
- `GraphEdge`
- `CanonicalPrimitive`
- `ApplicationGroup`
- `Dependency`
- `TargetDesign`
- `ReadinessFinding`
- `RiskScore`
- `CommercialEstimate`
- `AgentUsageRecord`
- `MigrationBlueprint`
- `Approval`
- `WorkflowRun`
- `GeneratedArtifact`
- `ValidationCheck`
- `EvidenceRecord`

Important relationships:

```text
Project has many SourceConnectors
Project has one or more TargetConnectors
SourceConnector produces GraphNodes and GraphEdges
GraphNodes map to CanonicalPrimitives
ApplicationGroup contains CanonicalPrimitives
TargetDesign projects CanonicalPrimitives into target resources
CommercialEstimate prices TargetDesign and MigrationBlueprint scope
MigrationBlueprint references TargetDesign and CommercialEstimate
WorkflowRun executes MigrationBlueprint
ValidationCheck produces EvidenceRecord
```

## 15. Trust and Safety Model

OmniBridge should earn trust through separation of responsibilities.

### Deterministic source of truth

Inventory, graph records, rules, workflow state, approvals, and validation results are structured records. They are not freeform AI claims.

### Rules before explanations

Blocker detection should be deterministic. AI explains blockers and suggests remediation, but the rule engine decides whether a blocker exists.

### Approval gates

Approval should be required for:

- source credential changes
- migration scope approval
- commercial estimate approval
- target design approval
- Azure resource creation
- source snapshot creation or deletion
- source VM shutdown
- production cutover
- firewall or NSG changes
- decommissioning

### Auditability

Every recommendation, estimate revision, approval, generated artifact, migration action, and validation result should be traceable.

## 16. Differentiators

OmniBridge should not be positioned as "Azure Migrate with AI."

The differentiators are:

- canonical graph of enterprise technology primitives
- corridor-based migration factory architecture
- agent-generated application grouping and dependency analysis
- pre-sales estimate and SOW generation from real discovery data
- approved estimates linked directly to migration blueprints
- repeatable MSP delivery model
- target architecture generation
- IaC and runbook generation
- explainable readiness and risk scoring
- human approval only where judgment or risk requires it
- validation evidence as a first-class deliverable
- future support for infrastructure, cloud, and platform migration corridors

## 17. Success Metrics

Product metrics:

- time from first connection to usable estate graph
- time from discovery to customer estimate
- time from estimate to approved blueprint
- percentage of workloads auto-classified with high confidence
- percentage of findings explained without human engineer input
- number of human decision points per project
- agent/token usage per discovered asset
- estimate accuracy versus actual delivery effort
- blueprint change rate after approval
- migration wave success rate
- validation pass rate

Business metrics:

- assessment-to-migration conversion rate
- average project gross margin
- agent/token gross margin
- delivery hours saved per project
- projects managed per migration lead
- repeat projects per MSP partner
- expansion from VMware-to-Azure into additional corridors

## 18. Project Lifecycle and State Model

OmniBridge should model every migration as a project lifecycle, not as a loose set of screens or tasks. This matters because the lifecycle ties together discovery, pricing, SOW approval, blueprint approval, execution, validation, and change-order handling.

Recommended project states:

```text
LEAD_CREATED
   -> DISCOVERY_AUTHORIZED
   -> DISCOVERY_RUNNING
   -> GRAPH_READY
   -> ASSESSMENT_READY
   -> ESTIMATE_DRAFTED
   -> ESTIMATE_REVIEWED
   -> SOW_APPROVED
   -> BLUEPRINT_DRAFTED
   -> BLUEPRINT_APPROVED
   -> EXECUTION_READY
   -> TEST_MIGRATION_RUNNING
   -> TEST_VALIDATED
   -> AWAITING_CUTOVER_APPROVAL
   -> CUTOVER_RUNNING
   -> POST_CUTOVER_VALIDATING
   -> MIGRATION_COMPLETE
   -> CLOSEOUT_DELIVERED
```

Exception states:

```text
DISCOVERY_BLOCKED
ESTIMATE_EXPIRED
CHANGE_ORDER_REQUIRED
CUSTOMER_DECISION_REQUIRED
SECURITY_REVIEW_REQUIRED
EXECUTION_BLOCKED
VALIDATION_FAILED
ROLLBACK_RUNNING
PROJECT_PAUSED
PROJECT_CANCELLED
```

Each state should have:

- entry criteria
- exit criteria
- required artifacts
- required approvals
- responsible actor
- allowed agent actions
- allowed human actions
- audit events

Example:

```yaml
state: ESTIMATE_REVIEWED
entry_criteria:
  - canonical graph exists
  - assessment confidence >= 0.70
  - estimate generated
  - assumptions listed
required_artifacts:
  - assessment report
  - commercial estimate
  - scope assumptions
  - out-of-scope list
exit_criteria:
  - customer approves SOW
  - or estimate is revised
  - or project is paused
approval_required:
  - customer_scope_approval
  - commercial_approval
```

The lifecycle should also support partial progression. A customer may approve assessment but not execution. A partner may generate a blueprint before choosing the execution backend. A migration wave may be approved while another wave is blocked.

## 19. Canonical Graph Ontology

The canonical graph should be strict enough for automation and flexible enough to represent messy real-world environments.

### Node Identity

Every graph node should have:

- stable OmniBridge ID
- project ID
- source connector ID
- source object ID
- canonical primitive type
- platform-specific type
- observed name
- normalized name
- discovery timestamp
- last seen timestamp
- confidence score
- provenance record
- version

Example:

```yaml
id: node-omni-01hxyz
project_id: project-acme-vmware-azure
source_connector_id: vcenter-prod
source_object:
  platform: vmware
  type: VirtualMachine
  id: vm-12345
canonical:
  type: ComputeNode
  normalized_name: claims-api-01
confidence: 0.96
provenance:
  discovered_by: vcenter-collector
  observed_at: 2026-05-09T17:00:00Z
  evidence:
    - vcenter.vm.config
    - vcenter.vm.runtime
    - vmware_tools.guest_info
version: 4
```

### Core Edge Types

The first release should support these graph relationships:

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
- `GOVERNED_BY_POLICY`
- `HAS_COST_CENTER`
- `HAS_READINESS_FINDING`
- `PROJECTS_TO`
- `MIGRATES_TO`
- `VALIDATED_BY`

Edges should carry confidence, evidence, and source. A user-confirmed dependency is stronger than an inferred naming-pattern dependency. A packet-observed dependency is stronger than an AI guess.

Example:

```yaml
edge:
  type: DEPENDS_ON
  from: claims-api-01
  to: claims-db-01
  confidence: 0.91
  evidence:
    - observed_tcp_1433_flow
    - shared_application_group
    - naming_pattern
  confirmed_by_user: false
```

### Corrections and Project Memory

User corrections should become durable project rules.

Example:

```yaml
kind: project.rule
version: 1
scope: project-acme-vmware-azure
rule:
  if:
    vm_name_matches: "claims-db-old*"
  then:
    exclude_from_application: Claims Portal
    include_in_application: Legacy Reporting
source:
  created_by: jane.doe@example.com
  reason: customer owner correction during assessment
```

These rules should apply to future classification runs inside the same project and optionally be promoted to partner-level reusable patterns.

### Graph Versioning

The graph should be versioned as discovery improves. The product needs to answer:

- what changed since the last discovery
- which new assets appeared
- which assets disappeared
- which estimates changed
- which blueprints became stale
- which approvals need revalidation

Graph changes that affect approved scope, price, risk, or target design should trigger review.

## 20. Migration Corridor Interface

Every migration path should be implemented as a corridor. VMware-to-Azure is the first corridor, but the interface should support future corridors without rewriting the product.

Corridor responsibilities:

- discover or import source data
- map source objects to canonical primitives
- project canonical primitives into target design objects
- run corridor-specific readiness rules
- estimate cost, effort, and complexity
- generate artifacts
- call execution backends
- validate target state
- produce closeout evidence

Recommended corridor interface:

```text
discover()
map_to_canonical()
infer_dependencies()
project_to_target()
run_readiness()
estimate()
generate_blueprint()
generate_artifacts()
prepare_execution()
execute_step()
validate()
closeout()
```

Example corridor manifest:

```yaml
kind: migration.corridor
version: 1
name: vmware-to-azure
source_platforms:
  - vmware-vcenter
target_platforms:
  - azure
capabilities:
  discovery: true
  assessment: true
  target_design: true
  estimate: true
  blueprint: true
  iac_generation: true
  azure_migrate_orchestration: true
  custom_replication: false
execution_backends:
  - azure-migrate
  - manual-runbook
status: release-1
```

Corridors should declare whether they are:

- assessment-only
- design-capable
- execution-capable
- validation-capable
- custom-conversion-capable

This prevents the platform from overpromising support for future corridors before execution is actually implemented.

## 21. Estimation and Pricing Engine

The estimation engine is both a product feature and a sales vehicle. It should produce a customer-facing commercial estimate from real discovery data, not from a generic services spreadsheet.

The estimate should answer:

- what is in scope
- what is out of scope
- what is unknown
- what makes the work complex
- what the fixed project fee covers
- how much agent usage is included
- what usage or complexity creates overage
- what assumptions must hold
- what events trigger a change order
- how confident OmniBridge is in the estimate

### Estimation Inputs

Inputs:

- discovered assets
- in-scope assets
- asset types
- storage size
- network count
- application group count
- inferred dependency count
- blocker count
- unsupported feature count
- required target regions
- compliance requirements
- change window requirements
- Azure Migrate fit
- custom handling requirements
- discovery confidence
- customer-provided constraints
- prior similar projects

### Complexity Drivers

The engine should score:

- compute complexity
- storage complexity
- network complexity
- identity complexity
- dependency complexity
- compliance complexity
- readiness risk
- target architecture complexity
- validation complexity
- customer decision complexity
- unknowns and missing access

Example:

```yaml
complexity:
  compute: medium
  storage: high
  network: high
  identity: medium
  dependencies: high
  compliance: medium
  readiness: high
  overall_score: 78
  overall_band: high
```

### Pricing Shape

The internal pricing model can be explicit even if external packaging is simplified.

```text
project_price =
  base_corridor_package
  + estate_size_units
  + application_group_units
  + migration_wave_units
  + complexity_multiplier
  + risk_contingency
  + optional_delivery_services
  + included_agent_usage
```

The token/agent meter should estimate:

- discovery interpretation runs
- application grouping runs
- dependency reasoning runs
- target design runs
- readiness explanation runs
- estimate generation runs
- blueprint generation runs
- IaC and runbook generation runs
- validation and remediation runs
- customer report generation runs

The customer-facing version should show this as an included AI/agent usage allowance with clear overage rules.

### Change-Order Triggers

Approved estimates should become stale when reality changes materially.

Change-order triggers:

- in-scope asset count increases beyond agreed tolerance
- a new source platform appears
- a new target platform is requested
- custom conversion is required
- required access was not available during assessment
- dependency data materially changes the wave plan
- network redesign exceeds approved assumptions
- security/compliance requirements change
- validation requirements expand
- customer adds production cutover support not included in assessment
- agent usage exceeds included allowance because of customer-driven iterations

Example:

```yaml
change_order_policy:
  asset_count_tolerance: 0.15
  new_platform_requires_change_order: true
  custom_conversion_requires_change_order: true
  included_design_iterations: 3
  agent_usage_overage_threshold: 1.20
```

## 22. Agent Tooling and Decision Rights

Agents should be constrained by role, tools, and decision rights.

### Decision Rights

Agents may decide:

- naming suggestions
- classification proposals below approval threshold
- low-risk report wording
- draft blueprint edits
- documentation structure
- low-impact estimate explanations

Agents may recommend but need approval for:

- application group membership above materiality threshold
- target architecture
- network mappings
- SKU recommendations
- migration wave sequencing
- commercial estimate changes
- readiness remediation
- generated IaC promotion
- test migration execution

Agents may never directly perform:

- source VM shutdown
- production cutover
- source deletion
- decommissioning
- firewall or NSG changes in production
- credential changes
- arbitrary guest script execution
- ignoring failed validation checks
- changing approved commercial scope

### Agent Tool Contracts

Every tool call should have:

- typed input
- typed output
- permission level
- audit event
- project ID
- actor ID
- idempotency key when executing
- dry-run mode where applicable

Example:

```json
{
  "tool": "estimate_project_scope",
  "permission": "read_analysis",
  "args": {
    "project_id": "project-acme-vmware-azure",
    "corridor": "vmware-to-azure",
    "scope_id": "scope-v3"
  },
  "output_contract": "commercial_estimate.v1"
}
```

Execution tools should be separate from analysis tools. An agent that can explain a blocker does not automatically get the right to remediate it.

## 23. Security, Data Handling, and Appliance Model

The enterprise security model should be explicit from the first release.

### Appliance Pattern

The VMware-to-Azure corridor should use an on-prem appliance for customer environments.

The appliance should:

- run inside the customer network
- connect outbound only
- store credentials locally or in customer-approved secret stores
- collect vCenter inventory
- optionally collect dependency and guest metadata
- redact secrets before data leaves the environment
- stream only approved metadata to the control plane
- execute approved local tasks
- write local audit logs

The cloud control plane should:

- host UI and APIs
- manage projects
- store normalized metadata
- run agent reasoning on approved data
- manage approvals
- generate blueprints and reports
- coordinate workflow state
- integrate with Azure APIs
- store audit records

### Data Minimization

The product should classify collected data:

- required metadata
- optional metadata
- sensitive metadata
- prohibited data

Default collection should avoid:

- guest file contents
- application secrets
- private keys
- password material
- database row data
- customer source code
- full packet captures

If deeper collection is needed, it should require explicit project approval.

### Tenant Isolation and Audit

The platform should support:

- tenant-level isolation
- customer-level workspaces
- partner-level access boundaries
- role-based access control
- least-privilege source credentials
- least-privilege cloud credentials
- immutable audit events
- approval history
- generated artifact history
- agent action logs

Security review should be treated as a first-class project gate for enterprise customers.

## 24. Customer Deliverables

OmniBridge should generate professional deliverables that MSPs and consultants can sell and reuse.

Release 1 deliverables:

- estate discovery summary
- topology report
- application grouping report
- dependency and confidence report
- readiness and blocker report
- risk register
- target Azure architecture recommendation
- cost and effort estimate
- SOW scope package
- migration blueprint
- migration wave plan
- IaC draft package
- cutover runbook
- rollback plan
- validation test plan
- executive summary

Execution releases should add:

- test migration evidence report
- cutover evidence report
- validation report
- exception report
- closeout packet
- decommission recommendation report

Each deliverable should include:

- project identity
- source data snapshot
- graph version
- assumptions
- exclusions
- confidence level
- decision log
- approval status

## 25. Scope Drift and Change Orders

OmniBridge should detect when a project no longer matches the approved scope.

Scope drift signals:

- new assets discovered after SOW approval
- asset ownership changes
- new application dependencies found
- target design changed materially
- network mapping changed materially
- blocker count increased
- migration wave count increased
- customer requested additional environments
- validation scope expanded
- agent usage exceeded approved allowance

When drift is detected, the product should:

1. flag the affected estimate and blueprint
2. explain what changed
3. quantify impact
4. recommend whether a change order is needed
5. generate a change-order draft
6. require approval before expanding commercial scope

Example:

```yaml
kind: commercial.change_order
version: 1
project: acme-vmware-to-azure
reason: in_scope_assets_increased
previous_scope:
  compute_nodes: 420
new_scope:
  compute_nodes: 493
impact:
  additional_waves: 2
  estimated_agent_usage_increase: 0.18
  estimated_delivery_effort_increase_hours: 96
approval_required: true
```

## 26. Release 1 MVP Build Path

Release 1 should be built in layers so the product becomes useful before live execution exists.

### MVP 0: Static Demo Dataset

Purpose: prove the product story and UI without infrastructure risk.

Build:

- sample VMware estate fixtures
- canonical graph model
- estate map
- application grouping examples
- readiness findings
- estimate output
- blueprint output
- sample customer deliverables

### MVP 1: Import-Based Assessment

Purpose: support early demos and pilots with exported inventory.

Build:

- CSV/JSON inventory import
- vCenter export parser
- canonical mapper
- graph explorer
- estimator
- assessment report generator
- SOW package generator

### MVP 2: Live Read-Only Discovery

Purpose: connect to real vCenter with low customer risk.

Build:

- on-prem discovery appliance
- vCenter read-only connector
- inventory sync
- graph versioning
- discovery audit log
- source data redaction

### MVP 3: Azure Target Design

Purpose: turn assessment into target architecture.

Build:

- Azure subscription/region/SKU metadata integration
- network mapping assistant
- VM size recommendation
- disk recommendation
- target design object
- target design approval workflow

### MVP 4: Blueprint and Deliverables

Purpose: create the artifact customers approve.

Build:

- migration blueprint generator
- runbook generator
- IaC draft generator
- risk register
- executive summary
- approval package

### MVP 5: Azure Migrate Workflow Mapping

Purpose: bridge design into execution without owning replication yet.

Build:

- Azure Migrate project mapping
- migration wave tracking
- test migration status capture
- validation checklist
- exception workflow

## 27. Roadmap

### Release 1: VMware-to-Azure Design Copilot

- vCenter discovery
- canonical graph
- topology UI
- application grouping
- Azure target design
- readiness analysis
- cost and effort estimation
- SOW package generation
- blueprint generation
- IaC and runbook generation
- Azure Migrate workflow mapping

### Release 2: Migration Factory Execution

- deeper Azure Migrate orchestration
- test migration tracking
- validation evidence
- approval workflows
- wave dashboard
- exception management

### Release 3: Partner Operating System

- multi-customer workspace
- reusable estimate templates
- branded reports
- reusable migration patterns
- partner-level reporting
- agent usage pools

### Release 4: Custom Conversion Corridor

- powered-off VM conversion
- VMDK inspection
- VHD generation
- managed disk upload
- Azure VM hydration
- boot validation

### Release 5: Multi-Cloud Corridor Expansion

- VMware to AWS
- VMware to GCP
- AWS to Azure
- Azure to AWS
- cloud-to-cloud network and identity mapping

### Release 6: Platform Migration Corridors

- ML platform migration
- data platform migration
- pipeline and job migration
- model artifact mapping
- environment and dependency translation

## 28. Product Positioning

Short positioning:

> OmniBridge is an AI-assisted migration factory that turns messy enterprise environments into approved, priced, executable migration blueprints.

Long positioning:

> OmniBridge discovers source environments, builds a canonical technology graph, uses specialized agents to classify workloads and design target architectures, estimates cost and effort before the work begins, and executes approved migration workflows through deterministic engines with full validation evidence.

The core promise:

> Fewer people, faster assessments, clearer pricing, safer execution, and repeatable migration delivery.
