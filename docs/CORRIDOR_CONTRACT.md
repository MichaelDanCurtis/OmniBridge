# Migration Corridor Contract

## Purpose

A migration corridor is a strongly typed package that teaches OmniBridge how to move from one source environment to one target environment.

The core platform owns the factory:

- project lifecycle
- canonical graph
- estimation engine
- blueprint engine
- workflow engine
- approval model
- audit model
- agent runtime
- UI shell

Corridors own source-to-target migration knowledge:

- source object interpretation
- canonical mappings
- target projections
- corridor-specific readiness rules
- estimation multipliers
- generated artifact templates
- execution backend mapping
- validation checks

This keeps VMware-to-Azure from becoming hardcoded into the platform while still letting the first product corridor ship quickly.

## Directory Shape

Each corridor lives under `corridors/<source>-to-<target>/`.

Recommended structure:

```text
corridors/<corridor>/
  corridor.yaml
  README.md
  mappings/
  rules/
  prompts/
  artifacts/
  fixtures/
  src/
  tests/
```

The first release can start with manifest, documentation, fixtures, rules, and mappings before source code exists.

## Capability Levels

A corridor must declare its capability level instead of implying complete migration support.

Valid capabilities:

- `discovery`
- `assessment`
- `target_design`
- `estimation`
- `blueprint_generation`
- `artifact_generation`
- `execution_mapping`
- `execution_orchestration`
- `validation`
- `custom_conversion`

Capability status values:

- `planned`
- `prototype`
- `supported`
- `not_supported`

Example:

```yaml
capabilities:
  discovery: supported
  assessment: supported
  target_design: supported
  estimation: supported
  blueprint_generation: supported
  artifact_generation: prototype
  execution_mapping: prototype
  execution_orchestration: planned
  validation: planned
  custom_conversion: not_supported
```

## Required Interface

Every corridor should eventually implement these functions through the corridor SDK.

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

### `discover()`

Collects or imports source environment metadata.

Output:

- source inventory objects
- source object provenance
- collection warnings
- missing permission findings

### `map_to_canonical()`

Maps source-specific objects into canonical OmniBridge graph primitives.

Output:

- canonical graph nodes
- canonical graph edges
- mapping confidence
- source evidence

### `infer_dependencies()`

Finds likely application, service, network, identity, and data dependencies.

Output:

- dependency edges
- confidence scores
- evidence list
- user-review requirements

### `project_to_target()`

Projects canonical graph primitives into target design objects.

Output:

- target resources
- target mappings
- design alternatives
- decision points

### `run_readiness()`

Runs deterministic corridor-specific readiness checks.

Output:

- blockers
- warnings
- informational findings
- remediation options

### `estimate()`

Estimates cost, effort, complexity, agent usage, and change-order risk for this corridor.

Output:

- commercial estimate inputs
- corridor complexity score
- effort multipliers
- usage forecast
- assumptions
- exclusions

### `generate_blueprint()`

Creates the corridor-specific sections of a migration blueprint.

Output:

- source scope
- target projection
- migration waves
- approvals
- validation requirements
- rollback requirements

### `generate_artifacts()`

Creates customer-facing and engineering artifacts.

Output:

- assessment report sections
- target architecture sections
- IaC drafts
- runbook steps
- validation plan sections
- SOW sections

### `prepare_execution()`

Prepares execution against the supported backend without starting risky actions.

Output:

- backend project mapping
- execution plan
- required credentials
- preflight results
- approval requirements

### `execute_step()`

Runs one approved workflow step through a deterministic backend.

Output:

- execution status
- backend IDs
- logs
- audit events
- next state

### `validate()`

Validates target state after test migration, cutover, or remediation.

Output:

- validation results
- evidence records
- failed checks
- remediation recommendations

### `closeout()`

Produces final migration closeout artifacts.

Output:

- validation packet
- exception list
- decommission recommendations
- customer signoff packet

## Corridor Manifest

Every corridor must include `corridor.yaml`.

Required fields:

```yaml
kind: migration.corridor
version: 1
name: source-to-target
display_name: Source to Target
status: planned
source_platforms: []
target_platforms: []
capabilities: {}
execution_backends: []
canonical_primitives: []
required_connectors: []
optional_connectors: []
artifact_templates: []
readiness_rule_sets: []
validation_rule_sets: []
estimation_model: ""
approval_gates: []
```

## Boundary Rules

Corridors may:

- define mappings from source objects to canonical primitives
- define target projection rules
- define readiness checks
- define validation checks
- define artifact templates
- define estimate multipliers
- define backend execution mappings

Corridors must not:

- own tenant isolation
- own user authentication
- bypass approval gates
- write directly to the audit log without platform APIs
- mutate source or target systems outside workflow execution
- create untyped agent tools
- store raw credentials
- override global security policy

## Connector Relationship

Connectors are reusable API clients. Corridors compose connectors.

Example:

```text
vmware-to-azure corridor
  uses vmware-vcenter connector
  uses azure-arm connector
  uses azure-migrate connector
```

The VMware connector should not know that Azure exists. The Azure connector should not know that VMware exists. The corridor owns the transformation between them.

## Agent Relationship

Agents can use corridor tools, but they do not own execution.

Analysis tools:

- read source inventory
- inspect graph
- propose mappings
- propose target design
- explain readiness findings
- draft estimates
- draft artifacts

Execution tools:

- require explicit workflow state
- require approval IDs
- require idempotency keys
- produce audit events
- use deterministic connectors

## Versioning

Corridors should be versioned independently from the platform.

Versioned items:

- manifest version
- mapping schema
- readiness rules
- estimation model
- artifact templates
- validation rules

Approved migration blueprints should record the corridor version used to generate them.

