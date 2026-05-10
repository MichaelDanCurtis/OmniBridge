const summaryCards = [
  { label: "Compute nodes", value: "3", tone: "neutral" },
  { label: "Blockers", value: "1", tone: "critical" },
  { label: "Warnings", value: "1", tone: "warning" },
  { label: "Project fee", value: "$27,250", tone: "neutral" },
  { label: "Agent usage", value: "$1,800", tone: "neutral" },
];

const decisionQueue = [
  "Confirm whether claims-db-01 snapshot can be removed.",
  "Confirm Azure subnet mapping for database tier.",
  "Approve commercial estimate before blueprint execution.",
];

export default function App() {
  return (
    <main className="workspace-shell">
      <section className="workspace-header" aria-labelledby="workspace-title">
        <div>
          <p className="eyebrow">Release 1 MVP</p>
          <h1 id="workspace-title">OmniBridge Consultant Workspace</h1>
          <p className="workspace-subtitle">ACME VMware-to-Azure Assessment</p>
        </div>
        <button className="primary-action" type="button">
          Approve Estimate
        </button>
      </section>

      <section className="assessment-panel" aria-labelledby="assessment-title">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Migration case</p>
            <h2 id="assessment-title">Claims Portal</h2>
          </div>
          <span className="status-pill">Consultant review</span>
        </div>

        <div className="summary-grid" aria-label="Assessment summary">
          {summaryCards.map((card) => (
            <article className={`summary-card summary-card--${card.tone}`} key={card.label}>
              <span>{card.label}</span>
              <strong>{card.value}</strong>
            </article>
          ))}
        </div>
      </section>

      <section className="workspace-grid" aria-label="Consultant actions">
        <article className="work-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Decision queue</p>
              <h2>Items needing confirmation</h2>
            </div>
            <span className="count-badge">{decisionQueue.length}</span>
          </div>

          <ol className="decision-list">
            {decisionQueue.map((item) => (
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
              <dt>Client</dt>
              <dd>ACME</dd>
            </div>
            <div>
              <dt>Application</dt>
              <dd>Claims Portal</dd>
            </div>
            <div>
              <dt>Next step</dt>
              <dd>Approve Estimate</dd>
            </div>
          </dl>
        </article>
      </section>
    </main>
  );
}
