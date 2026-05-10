# Release 1 Implementation Concerns

This log captures the issues and open engineering risks from the eight-step Release 1 build slice.

## Current Concerns

- Neo4j persistence is wired through the repository boundary, but the normal test path still uses fake repositories and fixture payloads. Live persistence requires `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD`, plus a running Neo4j instance.
- The approval ledger is intentionally deterministic and visible in the API/UI, but it is still in-memory for the MVP. Production needs a transactional approval store with actor identity, timestamps, immutable audit history, and replay protection.
- The Azure Migrate adapter is a dry-run operation planner. It models the workflow and approval gates, but it does not call Azure Migrate APIs until credentials, API contracts, retries, and idempotency semantics are added.
- GraphRAG infrastructure knowledge is seeded as static graph objects and can now be imported through the API. The next step is to ingest vendor docs, corridor playbooks, customer standards, and prior migration outcomes into a versioned knowledge graph.
- Langfuse/token usage support currently reconciles local usage records against estimated tokens. Actual trace ingestion still needs the deployed Langfuse client wiring and trace IDs from the LangGraph runtime.
- The consultant workspace can approve gates, but those approvals are still local MVP state and are not persisted across API process restarts.
- Validation evidence is generated before test migration execution. Actual post-test migration evidence still needs Azure Migrate status ingestion and guest/application probe results.

## Near-Term Follow-Ups

- Persist approval records in Postgres and include `approved_at`, `actor`, `reason`, `source_trace_id`, and `request_hash`.
- Add Langfuse client initialization behind environment configuration and include token usage on each agent trace.
- Replace the Terraform draft placeholder VM assumptions with OS-aware VM resources, per-VM sizes, disk resources, NSGs, and network mappings from the target design.
- Persist validation evidence with test migration run IDs, timestamps, probe output, and exception disposition.
- Add customer-facing risk register and executive summary artifacts to round out the approval package.
