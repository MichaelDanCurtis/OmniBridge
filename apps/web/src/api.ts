export type GraphSummary = {
  compute_nodes: number;
  network_segments: number;
  applications: number;
  readiness_findings: number;
  blockers: number;
  warnings: number;
  total_storage_gb: number;
};

export type EstimateLineItem = {
  code: string;
  description: string;
  quantity: number;
  unit: string;
  unit_price_usd: number;
  total_usd: number;
};

export type CommercialEstimate = {
  project_package: string;
  pricing_model: string;
  asset_count: number;
  complexity_score: number;
  complexity_band: string;
  base_project_fee_usd: number;
  estimated_agent_usage_usd: number;
  estimated_agent_tokens: number;
  agent_token_rate_per_1k_usd: number;
  project_fee_line_items: EstimateLineItem[];
  agent_usage_line_items: EstimateLineItem[];
  assumptions: string[];
};

export type MigrationWave = {
  name: string;
  compute_nodes: string[];
  execution_backend: string;
};

export type MigrationBlueprint = {
  application_name: string;
  compute_node_names: string[];
  waves: MigrationWave[];
  approval_gates: string[];
};

export type AnalysisResult = {
  summary: string;
  requires_consultant_review: boolean;
  decision_points: string[];
};

export type ProjectContext = {
  name: string;
  corridor: string;
  source: {
    platform: string;
    vcenter: string;
    datacenter: string;
  };
  target: {
    cloud: string;
    region: string;
    resource_group: string;
  };
};

export type VmInventoryItem = {
  name: string;
  moid: string;
  cpu: number;
  memory_mb: number;
  guest_os: string;
  tools_status: string;
  snapshot_count: number;
  disk_gb: number;
  source_network: string;
  observed_ip: string;
  readiness: string;
  target: {
    region: string;
    resource_group: string;
    subnet: string;
    vm_size: string;
    disk_type: string;
  };
};

export type NetworkMapping = {
  source_portgroup: string;
  vlan: number;
  target_vnet: string;
  target_subnet: string;
  security_intent: string;
};

export type TopologyEdge = {
  source_id?: string;
  source_name: string;
  relationship_type: string;
  target_id?: string;
  target_name: string;
  confidence?: number;
  evidence?: string[];
};

export type TopologySummary = {
  node_counts: Record<string, number>;
  relationship_counts: Record<string, number>;
  edges: TopologyEdge[];
};

export type GraphIngestStatus = {
  source: string;
  node_count: number;
  edge_count: number;
  persisted: boolean;
  neo4j_configured: boolean;
};

export type CollectorSnapshot = {
  collector_id: string;
  status: "not_deployed" | "pending_registration" | "online" | "offline" | "revoked";
  vcenter: string;
  last_heartbeat_at: string | null;
  version: string | null;
  capabilities: string[];
};

export type DiscoveryRunSnapshot = {
  run_id: string | null;
  status: "not_started" | "queued" | "running" | "completed" | "failed";
  source: string;
  compute_nodes: number;
  network_segments: number;
  graph_nodes: number;
  graph_edges: number;
  estimate_ready: boolean;
};

export type IntakeSnapshot = {
  project_id: string;
  collector: CollectorSnapshot;
  discovery: DiscoveryRunSnapshot;
};

export type CollectorBootstrap = {
  project_id: string;
  collector: CollectorSnapshot;
  registration: {
    collector_id: string;
    registration_token: string;
    api_url: string;
    install_command: string;
  };
};

export type GraphImportResponse = {
  nodes: number;
  edges: number;
  persisted: boolean;
};

export type ApprovalRecord = {
  gate: string;
  status: string;
  actor: string | null;
  reason: string | null;
};

export type ProjectWorkflow = {
  state: string;
  approvals: ApprovalRecord[];
  pending_approval_count: number;
};

export type MigrationWaveCreation = {
  wave_id: string | null;
  status: string;
  selected_compute_nodes: string[];
  execution_backend: string;
  operation_count: number;
  approval_gates: string[];
  ready_count: number;
  blocked_count: number;
  blockers: Array<{
    name: string;
    readiness: string;
    message: string;
  }>;
  next_action: string;
};

export type RemediationPlan = {
  plan_id: string;
  status: string;
  task_count: number;
  tasks: Array<{
    task_id: string;
    target_name: string;
    rule_id: string;
    severity: string;
    owner_role: string;
    automation_mode: string;
    approval_required: boolean;
    recommended_action: string;
  }>;
  next_action: string;
};

export type ExecutionOperation = {
  name: string;
  execution_mode: string;
  approval_required: boolean;
  approval_gate: string | null;
  payload: Record<string, unknown>;
};

export type ExecutionPlan = {
  backend: string;
  execution_mode: string;
  wave_id: string;
  operations: ExecutionOperation[];
};

export type ValidationSummary = {
  total_checks: number;
  pending: number;
  passed: number;
  failed: number;
  blocked: number;
};

export type ValidationCheck = {
  check_id: string;
  target_name: string;
  status: string;
  evidence: string;
  remediation: string | null;
};

export type ValidationEvidence = {
  project_id: string;
  wave_id: string;
  summary: ValidationSummary;
  checks: ValidationCheck[];
};

export type ReadinessFinding = {
  rule_id: string;
  severity: string;
  target_node_id: string;
  target_name: string;
  message: string;
};

export type GeneratedArtifact = {
  label: string;
  href: string;
  kind: string;
};

export type WorkspaceData = {
  project: ProjectContext;
  summary: GraphSummary;
  inventory: {
    vms: VmInventoryItem[];
  };
  graph_ingest: GraphIngestStatus;
  intake: IntakeSnapshot;
  workflow: ProjectWorkflow;
  execution_plan: ExecutionPlan;
  validation_evidence: ValidationEvidence;
  topology: TopologySummary;
  network_mappings: NetworkMapping[];
  readiness: {
    blockers: number;
    warnings: number;
    findings: ReadinessFinding[];
  };
  target_design: {
    vnet: string;
    subnets: string[];
    vm_targets: Array<{
      name: string;
      vm_size: string;
      subnet: string;
      disk_type: string;
    }>;
  };
  estimate: CommercialEstimate;
  blueprint: MigrationBlueprint;
  analysis: AnalysisResult;
  artifact_href: string;
  artifacts: GeneratedArtifact[];
};

async function requestJson<T>(path: string): Promise<T> {
  const response = await fetch(path);

  if (!response.ok) {
    throw new Error(`Request failed for ${path}: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function loadWorkspaceData(): Promise<WorkspaceData> {
  return requestJson<WorkspaceData>("/workspace/release1-demo");
}

export async function loadApprovals(): Promise<ProjectWorkflow> {
  return requestJson<ProjectWorkflow>("/approvals/release1-demo");
}

export async function persistFixtureGraph(): Promise<GraphImportResponse> {
  const response = await fetch("/imports/vmware-fixture", {
    body: JSON.stringify({
      fixture_path: "corridors/vmware-to-azure/fixtures/release1-small-estate.json",
      persist_to_neo4j: true,
    }),
    headers: {
      "Content-Type": "application/json",
    },
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(`Graph persistence failed: ${response.status}`);
  }

  return response.json() as Promise<GraphImportResponse>;
}

export async function bootstrapCollector(): Promise<CollectorBootstrap> {
  const response = await fetch("/collectors/release1-demo/bootstrap", {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(`Collector bootstrap failed: ${response.status}`);
  }

  return response.json() as Promise<CollectorBootstrap>;
}

export async function loadLatestDiscoveryRun(): Promise<IntakeSnapshot> {
  return requestJson<IntakeSnapshot>("/discovery-runs/release1-demo/latest");
}

export async function startDiscoveryRun(): Promise<IntakeSnapshot> {
  const response = await fetch("/discovery-runs/release1-demo/start", {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(`Discovery run failed: ${response.status}`);
  }

  return response.json() as Promise<IntakeSnapshot>;
}

export async function createMigrationWave(
  computeNodes: string[],
): Promise<MigrationWaveCreation> {
  const response = await fetch("/migration-waves/release1-demo", {
    body: JSON.stringify({
      compute_nodes: computeNodes,
    }),
    headers: {
      "Content-Type": "application/json",
    },
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(`Migration wave creation failed: ${response.status}`);
  }

  return response.json() as Promise<MigrationWaveCreation>;
}

export async function loadCurrentMigrationWave(): Promise<MigrationWaveCreation> {
  return requestJson<MigrationWaveCreation>("/migration-waves/release1-demo/current");
}

export async function createRemediationPlan(
  computeNodes: string[],
): Promise<RemediationPlan> {
  const response = await fetch("/remediation-plans/release1-demo", {
    body: JSON.stringify({
      compute_nodes: computeNodes,
    }),
    headers: {
      "Content-Type": "application/json",
    },
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(`Remediation planning failed: ${response.status}`);
  }

  return response.json() as Promise<RemediationPlan>;
}

export async function approveGate(gate: string): Promise<ApprovalRecord> {
  const response = await fetch(`/approvals/release1-demo/${gate}/approve`, {
    body: JSON.stringify({
      actor: "consultant@example.com",
      reason: "Approved from Consultant Workspace.",
    }),
    headers: {
      "Content-Type": "application/json",
    },
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(`Approval failed for ${gate}: ${response.status}`);
  }

  return response.json() as Promise<ApprovalRecord>;
}
