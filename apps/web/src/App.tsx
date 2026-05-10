import { useEffect, useMemo, useState } from "react";

import {
  loadWorkspaceData,
  persistFixtureGraph,
  type GraphIngestStatus,
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
      <button className="primary-action" type="button">
        Approve Estimate
      </button>
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
  const [graphIngest, setGraphIngest] = useState<GraphIngestStatus>(data.graph_ingest);
  const [graphPersistError, setGraphPersistError] = useState<string | null>(null);
  const [isPersistingGraph, setIsPersistingGraph] = useState(false);
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
  const graphStatusLabel = graphIngest.persisted
    ? "Persisted to Neo4j"
    : graphIngest.neo4j_configured
      ? "Ready to persist"
      : "Neo4j not configured";

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

  return (
    <main className="workspace-shell">
      <WorkspaceHeader projectTitle={data.project.name} />

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
              <span className="count-badge">{data.workflow.pending_approval_count} pending</span>
            </div>
            <div className="metric-grid">
              <div>
                <span>Current state</span>
                <strong>{data.workflow.state}</strong>
              </div>
            </div>
            <ul className="approval-list">
              {data.workflow.approvals.map((approval) => (
                <li key={approval.gate}>
                  <span>{approval.gate}</span>
                  <strong>{approval.status}</strong>
                </li>
              ))}
            </ul>
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
