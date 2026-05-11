import { useEffect, useMemo, useState } from "react";

import {
  approveGate,
  createMigrationWave,
  deployCollector,
  loadWorkspaceData,
  persistFixtureGraph,
  startDiscoveryRun,
  type GraphIngestStatus,
  type IntakeSnapshot,
  type MigrationWaveCreation,
  type ProjectWorkflow,
  type WorkspaceData,
} from "./api";

const FALLBACK_PROJECT_TITLE = "ACME VMware-to-Azure Assessment";

type SummaryCard = {
  label: string;
  value: string;
  tone: "neutral" | "critical" | "warning";
};

const currencyFormatter = new Intl.NumberFormat("en-US", {
  currency: "USD",
  maximumFractionDigits: 0,
  style: "currency",
});
const rateFormatter = new Intl.NumberFormat("en-US", {
  currency: "USD",
  maximumFractionDigits: 2,
  minimumFractionDigits: 2,
  style: "currency",
});

function formatCurrency(value: number): string {
  return currencyFormatter.format(value);
}

function formatMemory(memoryMb: number): string {
  return `${Math.round(memoryMb / 1024)} GB`;
}

function formatStorage(storageGb: number): string {
  return `${storageGb.toLocaleString("en-US")} GB`;
}

function formatTokens(tokens: number): string {
  return `${tokens.toLocaleString("en-US")} tokens`;
}

function formatTokenRate(rate: number): string {
  return `${rateFormatter.format(rate)} / 1k tokens`;
}

function formatUnitPrice(value: number): string {
  if (value > 0 && value < 1) {
    return rateFormatter.format(value);
  }

  return formatCurrency(value);
}

function formatQuantity(quantity: number, unit: string): string {
  return `${quantity.toLocaleString("en-US")} ${unit}`;
}

function WorkspaceHeader({ projectTitle = FALLBACK_PROJECT_TITLE }: { projectTitle?: string }) {
  return (
    <section className="workspace-header" aria-labelledby="workspace-title">
      <div>
        <p className="eyebrow">Release 1 MVP</p>
        <h1 id="workspace-title">OmniBridge Consultant Workspace</h1>
        <p className="workspace-subtitle">{projectTitle}</p>
      </div>
      <span className="status-pill">Migration intake</span>
    </section>
  );
}

function WorkspaceLoading() {
  return (
    <main className="workspace-shell">
      <WorkspaceHeader />
      <section className="assessment-panel" aria-live="polite">
        <p className="loading-message">Loading workspace data...</p>
      </section>
    </main>
  );
}

function WorkspaceError() {
  return (
    <main className="workspace-shell">
      <WorkspaceHeader />
      <section className="assessment-panel" role="alert">
        <p className="error-title">Unable to load workspace data.</p>
        <p className="error-message">
          Confirm the OmniBridge API is running, then refresh the workspace.
        </p>
      </section>
    </main>
  );
}

function WorkspaceLoaded({ data }: { data: WorkspaceData }) {
  const [intake, setIntake] = useState<IntakeSnapshot>(data.intake);
  const [selectedScope, setSelectedScope] = useState<string[]>(
    data.target_design.vm_targets.map((target) => target.name),
  );
  const [graphIngest, setGraphIngest] = useState<GraphIngestStatus>(data.graph_ingest);
  const [workflow, setWorkflow] = useState<ProjectWorkflow>(data.workflow);
  const [graphPersistError, setGraphPersistError] = useState<string | null>(null);
  const [isPersistingGraph, setIsPersistingGraph] = useState(false);
  const [intakeError, setIntakeError] = useState<string | null>(null);
  const [isDeployingCollector, setIsDeployingCollector] = useState(false);
  const [isRunningDiscovery, setIsRunningDiscovery] = useState(false);
  const [approvalError, setApprovalError] = useState<string | null>(null);
  const [approvingGate, setApprovingGate] = useState<string | null>(null);
  const [migrationWave, setMigrationWave] = useState<MigrationWaveCreation | null>(null);
  const [migrationWaveError, setMigrationWaveError] = useState<string | null>(null);
  const [isCreatingMigrationWave, setIsCreatingMigrationWave] = useState(false);
  const summaryCards = useMemo<SummaryCard[]>(
    () => [
      {
        label: "Compute nodes",
        tone: "neutral",
        value: data.summary.compute_nodes.toString(),
      },
      {
        label: "Networks",
        tone: "neutral",
        value: data.summary.network_segments.toString(),
      },
      {
        label: "Blockers",
        tone: data.summary.blockers > 0 ? "critical" : "neutral",
        value: data.summary.blockers.toString(),
      },
      {
        label: "Storage",
        tone: "neutral",
        value: formatStorage(data.summary.total_storage_gb),
      },
      {
        label: "Project fee",
        tone: "neutral",
        value: formatCurrency(data.estimate.base_project_fee_usd),
      },
      {
        label: "Agent usage",
        tone: "neutral",
        value: formatCurrency(data.estimate.estimated_agent_usage_usd),
      },
    ],
    [data],
  );
  const statusLabel = data.analysis.requires_consultant_review ? "Consultant review" : "Ready";
  const nextStep = data.analysis.requires_consultant_review
    ? "Resolve decision queue"
    : "Approve Estimate";
  const topologyNodeCounts = useMemo(
    () =>
      Object.entries(data.topology.node_counts)
        .filter(([label]) => !label.startsWith("VMware"))
        .sort(([left], [right]) => left.localeCompare(right)),
    [data.topology.node_counts],
  );
  const topologyRelationshipCounts = useMemo(
    () =>
      Object.entries(data.topology.relationship_counts).sort(([left], [right]) =>
        left.localeCompare(right),
      ),
    [data.topology.relationship_counts],
  );
  const topologyEdges = data.topology.edges.slice(0, 8);
  const validationChecks = data.validation_evidence.checks.slice(0, 8);
  const commercialEstimateApproval = workflow.approvals.find(
    (approval) => approval.gate === "commercial_estimate_approval",
  );
  const isEstimateApproved = commercialEstimateApproval?.status === "approved";
  const canReviewEstimate = intake.discovery.estimate_ready;
  const canSelectScope = canReviewEstimate && isEstimateApproved;
  const migrationCandidates = data.target_design.vm_targets.map((target) => {
    const inventory = data.inventory.vms.find((vm) => vm.name === target.name);
    return {
      ...target,
      readiness: inventory?.readiness ?? "Ready",
      source_network: inventory?.source_network ?? "unmapped",
    };
  });
  const graphStatusLabel = graphIngest.persisted
    ? "Persisted to Neo4j"
    : graphIngest.neo4j_configured
      ? "Ready to persist"
      : "Neo4j not configured";
  const collectorLabel =
    intake.discovery.status === "completed"
      ? "Discovery complete"
      : intake.collector.status === "connected"
        ? `Connected to ${intake.collector.vcenter}`
        : "Collector not deployed";
  const collectionLabel = intake.discovery.estimate_ready
    ? `${intake.discovery.compute_nodes} VMs discovered`
    : "Awaiting collection";

  async function handleDeployCollector() {
    setIsDeployingCollector(true);
    setIntakeError(null);
    try {
      setIntake(await deployCollector());
    } catch {
      setIntakeError("Collector deployment failed");
    } finally {
      setIsDeployingCollector(false);
    }
  }

  async function handleRunDataCollection() {
    setIsRunningDiscovery(true);
    setIntakeError(null);
    try {
      const snapshot = await startDiscoveryRun();
      setIntake(snapshot);
      setGraphIngest((current) => ({
        ...current,
        edge_count: snapshot.discovery.graph_edges,
        node_count: snapshot.discovery.graph_nodes,
        source: snapshot.discovery.source,
      }));
    } catch {
      setIntakeError("Discovery run failed");
    } finally {
      setIsRunningDiscovery(false);
    }
  }

  function handleToggleScope(name: string) {
    setSelectedScope((current) =>
      current.includes(name)
        ? current.filter((candidateName) => candidateName !== name)
        : [...current, name],
    );
  }

  async function handlePersistGraph() {
    setIsPersistingGraph(true);
    setGraphPersistError(null);
    try {
      const result = await persistFixtureGraph();
      setGraphIngest({
        ...graphIngest,
        edge_count: result.edges,
        node_count: result.nodes,
        persisted: result.persisted,
      });
    } catch {
      setGraphPersistError("Graph persistence failed");
    } finally {
      setIsPersistingGraph(false);
    }
  }

  async function handleApproveGate(gate: string) {
    setApprovingGate(gate);
    setApprovalError(null);
    try {
      const approved = await approveGate(gate);
      const approvals = workflow.approvals.map((approval) =>
        approval.gate === gate ? approved : approval,
      );
      setWorkflow({
        ...workflow,
        approvals,
        pending_approval_count: approvals.filter((approval) => approval.status === "pending")
          .length,
      });
    } catch {
      setApprovalError(`Approval failed for ${gate}`);
    } finally {
      setApprovingGate(null);
    }
  }

  async function handleCreateMigrationWave() {
    setIsCreatingMigrationWave(true);
    setMigrationWaveError(null);
    try {
      setMigrationWave(await createMigrationWave(selectedScope));
    } catch {
      setMigrationWaveError("Migration wave creation failed");
    } finally {
      setIsCreatingMigrationWave(false);
    }
  }

  return (
    <main className="workspace-shell">
      <WorkspaceHeader projectTitle={data.project.name} />

      <section className="workflow-panel" aria-label="Migration workflow">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Operator workflow</p>
            <h2>Migration intake</h2>
          </div>
          <span className="count-badge">3 stages</span>
        </div>

        <div className="workflow-grid">
          <article className="workflow-card workflow-card--active">
            <div className="workflow-card-heading">
              <span className="step-marker">1</span>
              <div>
                <p className="eyebrow">Source environment</p>
                <h2>VMware ingress</h2>
              </div>
            </div>
            <dl className="workflow-facts">
              <div>
                <dt>vCenter</dt>
                <dd>{data.project.source.vcenter}</dd>
              </div>
              <div>
                <dt>Collector</dt>
                <dd>{collectorLabel}</dd>
              </div>
              <div>
                <dt>Collection</dt>
                <dd>{collectionLabel}</dd>
              </div>
            </dl>
            <div className="workflow-actions">
              <button
                className="primary-action"
                disabled={intake.collector.status !== "not_deployed" || isDeployingCollector}
                onClick={() => void handleDeployCollector()}
                type="button"
              >
                {intake.collector.status === "not_deployed"
                  ? isDeployingCollector
                    ? "Deploying..."
                    : "Deploy collector"
                  : "Collector deployed"}
              </button>
              <button
                className="secondary-action"
                disabled={
                  intake.collector.status === "not_deployed" ||
                  intake.discovery.estimate_ready ||
                  isRunningDiscovery
                }
                onClick={() => void handleRunDataCollection()}
                type="button"
              >
                {intake.discovery.estimate_ready
                  ? "Collection complete"
                  : isRunningDiscovery
                    ? "Collecting..."
                    : "Run data collection"}
              </button>
            </div>
          </article>

          <article className={`workflow-card ${canReviewEstimate ? "workflow-card--active" : ""}`}>
            <div className="workflow-card-heading">
              <span className="step-marker">2</span>
              <div>
                <p className="eyebrow">Commercial gate</p>
                <h2>Cost estimate</h2>
              </div>
            </div>
            <span className="workflow-lock">
              {canReviewEstimate
                ? isEstimateApproved
                  ? "Estimate approved"
                  : "Ready for approval"
                : "Locked until discovery"}
            </span>
            <dl className="workflow-facts">
              <div>
                <dt>Project fee</dt>
                <dd>
                  {canReviewEstimate
                    ? `${formatCurrency(data.estimate.base_project_fee_usd)} project fee`
                    : "Pending discovery"}
                </dd>
              </div>
              <div>
                <dt>Agent usage</dt>
                <dd>
                  {canReviewEstimate
                    ? formatCurrency(data.estimate.estimated_agent_usage_usd)
                    : "Pending discovery"}
                </dd>
              </div>
              <div>
                <dt>Complexity</dt>
                <dd>{canReviewEstimate ? data.estimate.complexity_band : "Pending discovery"}</dd>
              </div>
            </dl>
            <div className="workflow-actions">
              <button
                className="primary-action"
                disabled={!canReviewEstimate || isEstimateApproved || approvingGate !== null}
                onClick={() => void handleApproveGate("commercial_estimate_approval")}
                type="button"
              >
                {isEstimateApproved ? "Approved" : "Approve estimate package"}
              </button>
            </div>
          </article>

          <article className={`workflow-card ${canSelectScope ? "workflow-card--active" : ""}`}>
            <div className="workflow-card-heading">
              <span className="step-marker">3</span>
              <div>
                <p className="eyebrow">Migration factory</p>
                <h2>Migration scope</h2>
              </div>
            </div>
            <span className="workflow-lock">
              {migrationWave
                ? `Wave ${migrationWave.wave_id} staged`
                : canSelectScope
                ? `${selectedScope.length} ${selectedScope.length === 1 ? "VM" : "VMs"} selected for wave-001`
                : "Locked until estimate approval"}
            </span>
            <ul className="scope-list">
              {migrationCandidates.map((candidate) => (
                <li key={candidate.name}>
                  <label>
                    <input
                      aria-label={candidate.name}
                      checked={selectedScope.includes(candidate.name)}
                      disabled={!canSelectScope || migrationWave !== null}
                      onChange={() => handleToggleScope(candidate.name)}
                      type="checkbox"
                    />
                    <span>{candidate.name}</span>
                  </label>
                  <small>
                    {candidate.source_network} -&gt; {candidate.subnet} / {candidate.vm_size} /{" "}
                    {candidate.readiness}
                  </small>
                </li>
              ))}
            </ul>
            <div className="workflow-actions">
              <button
                className="primary-action"
                disabled={
                  !canSelectScope ||
                  selectedScope.length === 0 ||
                  isCreatingMigrationWave ||
                  migrationWave !== null
                }
                onClick={() => void handleCreateMigrationWave()}
                type="button"
              >
                {migrationWave
                  ? "Wave created"
                  : isCreatingMigrationWave
                    ? "Creating wave..."
                    : "Create migration wave"}
              </button>
            </div>
            {migrationWave ? (
              <dl className="workflow-facts workflow-facts--compact">
                <div>
                  <dt>Backend</dt>
                  <dd>{migrationWave.execution_backend}</dd>
                </div>
                <div>
                  <dt>Operations</dt>
                  <dd>{migrationWave.operation_count}</dd>
                </div>
                <div>
                  <dt>Blocked</dt>
                  <dd>{migrationWave.blocked_count}</dd>
                </div>
                <div>
                  <dt>Next action</dt>
                  <dd>{migrationWave.next_action}</dd>
                </div>
              </dl>
            ) : null}
            {migrationWave?.blockers.length ? (
              <ul className="scope-list">
                {migrationWave.blockers.map((blocker) => (
                  <li key={blocker.name}>
                    <strong>{blocker.name}</strong>
                    <small>{blocker.message}</small>
                  </li>
                ))}
              </ul>
            ) : null}
          </article>
        </div>
        {intakeError ? <p className="error-message">{intakeError}</p> : null}
        {approvalError ? <p className="error-message">{approvalError}</p> : null}
        {migrationWaveError ? <p className="error-message">{migrationWaveError}</p> : null}
      </section>

      <section className="assessment-panel" aria-labelledby="assessment-title">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Migration case</p>
            <h2 id="assessment-title">{data.blueprint.application_name}</h2>
          </div>
          <span className="status-pill">{statusLabel}</span>
        </div>

        <div className="summary-grid" aria-label="Assessment summary">
          {summaryCards.map((card) => (
            <article className={`summary-card summary-card--${card.tone}`} key={card.label}>
              <span>{card.label}</span>
              <strong>{card.value}</strong>
            </article>
          ))}
        </div>

        <div className="context-strip" aria-label="Project context">
          <span>{data.project.source.vcenter}</span>
          <span>{data.project.target.region}</span>
          <span>{data.project.target.resource_group}</span>
          <span>{data.target_design.vnet}</span>
        </div>
        <p className="analysis-summary">{data.analysis.summary}</p>
      </section>

      <section className="workspace-grid" aria-label="Consultant actions">
        <article className="work-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Decision queue</p>
              <h2>Items needing confirmation</h2>
            </div>
            <span className="count-badge">{data.analysis.decision_points.length}</span>
          </div>

          <ol className="decision-list">
            {data.analysis.decision_points.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
        </article>

        <article className="work-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Test migration</p>
              <h2>Validation evidence</h2>
            </div>
            <span className="count-badge">
              {data.validation_evidence.summary.total_checks} checks
            </span>
          </div>
          <div className="metric-grid">
            <div>
              <span>Pending</span>
              <strong>{data.validation_evidence.summary.pending}</strong>
            </div>
            <div>
              <span>Blocked</span>
              <strong>{data.validation_evidence.summary.blocked}</strong>
            </div>
            <div>
              <span>Passed</span>
              <strong>{data.validation_evidence.summary.passed}</strong>
            </div>
          </div>
          <ul className="validation-list">
            {validationChecks.map((check) => (
              <li key={`${check.target_name}-${check.check_id}`}>
                <div>
                  <strong>{check.check_id}</strong>
                  <span>{check.target_name}</span>
                </div>
                <p>{check.remediation ?? check.evidence}</p>
                <span className={`validation-status validation-status--${check.status}`}>
                  {check.status}
                </span>
              </li>
            ))}
          </ul>
        </article>

        <article className="work-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Execution readiness</p>
              <h2>Blueprint approval</h2>
            </div>
          </div>
          <dl className="readiness-list">
            <div>
              <dt>Application</dt>
              <dd>{data.blueprint.application_name}</dd>
            </div>
            <div>
              <dt>Assets</dt>
              <dd>{data.estimate.asset_count} VMs</dd>
            </div>
            <div>
              <dt>Backend</dt>
              <dd>{data.blueprint.waves[0]?.execution_backend ?? "Unassigned"}</dd>
            </div>
            <div>
              <dt>Next step</dt>
              <dd>{nextStep}</dd>
            </div>
          </dl>
          <div className="approval-section">
            <div className="approval-heading">
              <div>
                <p className="eyebrow">Workflow state</p>
                <h2>Approval ledger</h2>
              </div>
              <span className="count-badge">{workflow.pending_approval_count} pending</span>
            </div>
            <div className="metric-grid">
              <div>
                <span>Current state</span>
                <strong>{workflow.state}</strong>
              </div>
            </div>
            <ul className="approval-list">
              {workflow.approvals.map((approval) => (
                <li key={approval.gate}>
                  <span>{approval.gate}</span>
                  <div className="approval-actions">
                    <strong>{approval.status}</strong>
                    {approval.status === "pending" ? (
                      <button
                        className="inline-action"
                        disabled={approvingGate === approval.gate}
                        onClick={() => void handleApproveGate(approval.gate)}
                        type="button"
                      >
                        {approvingGate === approval.gate
                          ? "Approving..."
                          : `Approve ${approval.gate}`}
                      </button>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
            {approvalError ? <p className="error-message">{approvalError}</p> : null}
          </div>
          <div className="artifact-section">
            <p className="eyebrow">Generated artifacts</p>
            <div className="artifact-links">
              {data.artifacts.map((artifact) => (
                <a className="secondary-link" href={artifact.href} key={artifact.href}>
                  <span>{artifact.label}</span>
                  <small>{artifact.kind}</small>
                </a>
              ))}
            </div>
          </div>
        </article>
      </section>

      <section className="workspace-grid workspace-grid--balanced" aria-label="Commercial details">
        <article className="work-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Commercial model</p>
              <h2>Estimate breakdown</h2>
            </div>
            <span className="count-badge">{data.estimate.complexity_band}</span>
          </div>

          <div className="metric-grid" aria-label="Token pricing">
            <div>
              <span>Pricing model</span>
              <strong>{data.estimate.pricing_model}</strong>
            </div>
            <div>
              <span>Estimated tokens</span>
              <strong>{formatTokens(data.estimate.estimated_agent_tokens)}</strong>
            </div>
            <div>
              <span>Token rate</span>
              <strong>{formatTokenRate(data.estimate.agent_token_rate_per_1k_usd)}</strong>
            </div>
          </div>

          <ul className="estimate-list">
            {data.estimate.project_fee_line_items.map((item) => (
              <li key={item.code}>
                <div>
                  <strong>{item.code}</strong>
                  <span>{item.description}</span>
                </div>
                <span>
                  {formatQuantity(item.quantity, item.unit)} x {formatUnitPrice(item.unit_price_usd)}
                </span>
                <strong>{formatCurrency(item.total_usd)}</strong>
              </li>
            ))}
            {data.estimate.agent_usage_line_items.map((item) => (
              <li key={item.code}>
                <div>
                  <strong>{item.code}</strong>
                  <span>{item.description}</span>
                </div>
                <span>
                  {formatQuantity(item.quantity, item.unit)} x {formatUnitPrice(item.unit_price_usd)}
                </span>
                <strong>{formatCurrency(item.total_usd)}</strong>
              </li>
            ))}
          </ul>
        </article>

        <article className="work-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Approval package</p>
              <h2>SOW assumptions</h2>
            </div>
          </div>
          <ul className="assumption-list">
            {data.estimate.assumptions.map((assumption) => (
              <li key={assumption}>{assumption}</li>
            ))}
          </ul>
        </article>
      </section>

      <section className="workspace-grid workspace-grid--balanced" aria-label="Execution mapping">
        <article className="work-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Backend adapter</p>
              <h2>Azure Migrate execution plan</h2>
            </div>
            <span className="status-pill">{data.execution_plan.execution_mode}</span>
          </div>
          <div className="metric-grid">
            <div>
              <span>Backend</span>
              <strong>{data.execution_plan.backend}</strong>
            </div>
            <div>
              <span>Wave</span>
              <strong>{data.execution_plan.wave_id}</strong>
            </div>
            <div>
              <span>Operations</span>
              <strong>{data.execution_plan.operations.length}</strong>
            </div>
          </div>
          <ul className="operation-list">
            {data.execution_plan.operations.map((operation, index) => (
              <li key={`${operation.name}-${index}`}>
                <div>
                  <strong>{operation.name}</strong>
                  <span>{operation.execution_mode}</span>
                </div>
                {operation.approval_gate ? (
                  <span className="status-pill">{operation.approval_gate}</span>
                ) : null}
              </li>
            ))}
          </ul>
        </article>
      </section>

      <section className="workspace-grid workspace-grid--balanced" aria-label="Canonical topology">
        <article className="work-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Knowledge substrate</p>
              <h2>Graph primitives</h2>
            </div>
            <span className="count-badge">{topologyNodeCounts.length}</span>
          </div>
          <ul className="topology-count-list">
            {topologyNodeCounts.map(([label, count]) => (
              <li key={label}>
                <strong>
                  {label}: {count}
                </strong>
              </li>
            ))}
          </ul>
          <div className="relationship-cloud" aria-label="Relationship counts">
            {topologyRelationshipCounts.map(([relationship, count]) => (
              <span key={relationship}>
                {relationship}: {count}
              </span>
            ))}
          </div>
        </article>

        <article className="work-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Neo4j projection</p>
              <h2>Canonical graph</h2>
            </div>
            <span className="count-badge">{data.topology.edges.length}</span>
          </div>
          <ul className="topology-edge-list">
            {topologyEdges.map((edge) => (
              <li key={`${edge.source_name}-${edge.relationship_type}-${edge.target_name}`}>
                <span>{edge.source_name}</span>
                <strong>{edge.relationship_type}</strong>
                <span>{edge.target_name}</span>
              </li>
            ))}
          </ul>
        </article>
      </section>

      <section className="workspace-grid workspace-grid--balanced" aria-label="Graph operations">
        <article className="work-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Discovery import</p>
              <h2>Graph persistence</h2>
            </div>
            <span className="status-pill">{graphStatusLabel}</span>
          </div>
          <div className="metric-grid">
            <div>
              <span>Import source</span>
              <strong>{graphIngest.source}</strong>
            </div>
            <div>
              <span>Graph size</span>
              <strong>
                {graphIngest.node_count} nodes / {graphIngest.edge_count} edges
              </strong>
            </div>
            <div>
              <span>Repository</span>
              <strong>{graphIngest.neo4j_configured ? "Neo4j configured" : "Neo4j not configured"}</strong>
            </div>
          </div>
          <button
            className="secondary-action"
            disabled={isPersistingGraph}
            onClick={handlePersistGraph}
            type="button"
          >
            {isPersistingGraph ? "Persisting..." : "Persist to Neo4j"}
          </button>
          {graphPersistError ? <p className="error-message">{graphPersistError}</p> : null}
        </article>
      </section>

      <section className="workspace-grid workspace-grid--balanced" aria-label="Estate details">
        <article className="work-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Discovered estate</p>
              <h2>Estate inventory</h2>
            </div>
            <span className="count-badge">{data.inventory.vms.length}</span>
          </div>
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th scope="col">VM</th>
                  <th scope="col">Source</th>
                  <th scope="col">Target</th>
                  <th scope="col">Readiness</th>
                </tr>
              </thead>
              <tbody>
                {data.inventory.vms.map((vm) => (
                  <tr key={vm.name}>
                    <td>
                      <strong>{vm.name}</strong>
                      <span>
                        {vm.cpu} vCPU / {formatMemory(vm.memory_mb)} / {formatStorage(vm.disk_gb)}
                      </span>
                    </td>
                    <td>
                      <strong>{vm.source_network}</strong>
                      <span>{vm.observed_ip}</span>
                    </td>
                    <td>
                      <strong>{vm.target.vm_size}</strong>
                      <span>
                        {vm.target.subnet} / {vm.target.disk_type}
                      </span>
                    </td>
                    <td>
                      <span className={`readiness-pill readiness-pill--${vm.readiness.toLowerCase().replace(" ", "-")}`}>
                        {vm.readiness}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>

        <article className="work-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Network design</p>
              <h2>Azure mappings</h2>
            </div>
          </div>
          <ul className="mapping-list">
            {data.network_mappings.map((mapping) => (
              <li key={mapping.source_portgroup}>
                <strong>
                  {mapping.source_portgroup} -&gt; {mapping.target_subnet}
                </strong>
                <span>
                  VLAN {mapping.vlan} / {mapping.target_vnet}
                </span>
                <p>{mapping.security_intent}</p>
              </li>
            ))}
          </ul>
        </article>
      </section>

      <section className="workspace-grid workspace-grid--balanced" aria-label="Validation details">
        <article className="work-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Preflight</p>
              <h2>Readiness findings</h2>
            </div>
            <span className="count-badge">
              {data.readiness.blockers} blocker / {data.readiness.warnings} warning
            </span>
          </div>
          <ul className="finding-list">
            {data.readiness.findings.map((finding) => (
              <li key={`${finding.rule_id}-${finding.target_node_id}`}>
                <div>
                  <strong>{finding.rule_id}</strong>
                  <span>{finding.target_name}</span>
                </div>
                <p>{finding.message}</p>
                <span className={`severity severity--${finding.severity}`}>{finding.severity}</span>
              </li>
            ))}
          </ul>
        </article>

        <article className="work-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Target design</p>
              <h2>Azure VM plan</h2>
            </div>
          </div>
          <ul className="target-list">
            {data.target_design.vm_targets.map((target) => (
              <li key={target.name}>
                <strong>{target.name}</strong>
                <span>{target.vm_size}</span>
                <span>
                  {target.subnet} / {target.disk_type}
                </span>
              </li>
            ))}
          </ul>
        </article>
      </section>
    </main>
  );
}

export default function App() {
  const [data, setData] = useState<WorkspaceData | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let isCurrent = true;

    loadWorkspaceData()
      .then((workspaceData) => {
        if (isCurrent) {
          setData(workspaceData);
        }
      })
      .catch(() => {
        if (isCurrent) {
          setError(true);
        }
      });

    return () => {
      isCurrent = false;
    };
  }, []);

  if (error) {
    return <WorkspaceError />;
  }

  if (!data) {
    return <WorkspaceLoading />;
  }

  return <WorkspaceLoaded data={data} />;
}
