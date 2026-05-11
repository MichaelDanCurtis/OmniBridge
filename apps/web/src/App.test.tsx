// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

describe("App", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("renders the consultant workspace from Release 1 API data", async () => {
    const workspaceResponse = {
      project: {
        name: "ACME VMware-to-Azure Assessment",
        source: {
          vcenter: "vcsa-prod-01",
        },
        target: {
          region: "westus2",
          resource_group: "rg-claims-prod",
        },
      },
      summary: {
        compute_nodes: 3,
        network_segments: 3,
        applications: 1,
        readiness_findings: 2,
        blockers: 1,
        warnings: 1,
        total_storage_gb: 1280,
      },
      graph_ingest: {
        source: "fixture",
        node_count: 12,
        edge_count: 13,
        persisted: false,
        neo4j_configured: false,
      },
      intake: {
        project_id: "project-acme-vmware-azure",
        collector: {
          collector_id: "collector-release1-demo",
          status: "not_deployed",
          vcenter: "vcsa-prod-01",
          last_heartbeat_at: null,
        },
        discovery: {
          run_id: null,
          status: "not_started",
          source: "fixture",
          compute_nodes: 0,
          network_segments: 0,
          graph_nodes: 0,
          graph_edges: 0,
          estimate_ready: false,
        },
      },
      workflow: {
        state: "BLUEPRINT_GENERATED",
        pending_approval_count: 6,
        approvals: [
          {
            gate: "commercial_estimate_approval",
            status: "pending",
            actor: null,
            reason: null,
          },
          {
            gate: "target_design_approval",
            status: "pending",
            actor: null,
            reason: null,
          },
          {
            gate: "blueprint_approval",
            status: "pending",
            actor: null,
            reason: null,
          },
          {
            gate: "test_migration_approval",
            status: "pending",
            actor: null,
            reason: null,
          },
          {
            gate: "source_shutdown_approval",
            status: "pending",
            actor: null,
            reason: null,
          },
          {
            gate: "cutover_approval",
            status: "pending",
            actor: null,
            reason: null,
          },
        ],
      },
      execution_plan: {
        backend: "azure-migrate",
        execution_mode: "dry_run",
        wave_id: "wave-001",
        operations: [
          {
            name: "ensure_migrate_project",
            execution_mode: "dry_run",
            approval_required: false,
            approval_gate: null,
            payload: {},
          },
          {
            name: "start_test_migration",
            execution_mode: "dry_run",
            approval_required: true,
            approval_gate: "test_migration_approval",
            payload: {},
          },
        ],
      },
      validation_evidence: {
        project_id: "project-acme-vmware-azure",
        wave_id: "wave-001",
        summary: {
          total_checks: 18,
          pending: 12,
          passed: 0,
          failed: 0,
          blocked: 6,
        },
        checks: [
          {
            check_id: "vm_boot",
            target_name: "claims-web-01",
            status: "pending",
            evidence: "Awaiting test migration execution.",
            remediation: null,
          },
          {
            check_id: "vm_boot",
            target_name: "claims-db-01",
            status: "blocked",
            evidence: "Awaiting test migration execution.",
            remediation: "Resolve preflight blockers before test migration.",
          },
        ],
      },
      topology: {
        node_counts: {
          ComputeNode: 3,
          NetworkSegment: 3,
          Host: 1,
          Datastore: 1,
          StorageVolume: 3,
        },
        relationship_counts: {
          CONNECTED_TO: 3,
          RUNS_ON: 3,
          HAS_VOLUME: 3,
          USES_DATASTORE: 3,
        },
        edges: [
          {
            source_name: "claims-db-01",
            relationship_type: "RUNS_ON",
            target_name: "esx01",
          },
          {
            source_name: "claims-db-01",
            relationship_type: "HAS_VOLUME",
            target_name: "claims-db-01-disk-0",
          },
        ],
      },
      estimate: {
        project_package: "assessment",
        pricing_model: "project_fee_plus_agent_token_usage",
        asset_count: 3,
        complexity_score: 6,
        complexity_band: "moderate",
        base_project_fee_usd: 27250,
        estimated_agent_usage_usd: 1800,
        estimated_agent_tokens: 9_000_000,
        agent_token_rate_per_1k_usd: 0.2,
        project_fee_line_items: [
          {
            code: "assessment_base",
            description: "Release 1 migration assessment package",
            quantity: 1,
            unit: "project",
            unit_price_usd: 25000,
            total_usd: 25000,
          },
          {
            code: "compute_node_assessment",
            description: "Per-VM discovery, readiness, target sizing, and blueprint review",
            quantity: 3,
            unit: "compute_node",
            unit_price_usd: 750,
            total_usd: 2250,
          },
        ],
        agent_usage_line_items: [
          {
            code: "estimated_agent_token_usage",
            description: "Estimated LangGraph agent analysis, artifact generation, and review loops",
            quantity: 9000,
            unit: "1k_tokens",
            unit_price_usd: 0.2,
            total_usd: 1800,
          },
        ],
        assumptions: [
          "Includes graph discovery",
          "Agent usage is estimated before execution and reconciled against actual token usage.",
        ],
      },
      blueprint: {
        application_name: "Claims Portal",
        compute_node_names: ["claims-web-01", "claims-api-01", "claims-db-01"],
        waves: [
          {
            name: "wave-001",
            compute_nodes: ["claims-web-01", "claims-api-01", "claims-db-01"],
            execution_backend: "azure-migrate",
          },
        ],
        approval_gates: [
          "test_migration_approval",
          "source_shutdown_approval",
          "cutover_approval",
        ],
      },
      analysis: {
        summary: "Claims Portal contains 3 compute nodes with 1 blocker and 1 warning.",
        requires_consultant_review: true,
        decision_points: [
          "Confirm whether claims-db-01 snapshot can be removed.",
          "Approve commercial estimate before blueprint execution.",
        ],
      },
      inventory: {
        vms: [
          {
            name: "claims-db-01",
            cpu: 8,
            memory_mb: 32768,
            disk_gb: 1024,
            source_network: "dvpg-db-prod",
            observed_ip: "10.20.30.31",
            readiness: "Blocked",
            target: {
              vm_size: "Standard_D8s_v5",
              subnet: "snet-db",
              disk_type: "Premium SSD",
            },
          },
        ],
      },
      network_mappings: [
        {
          source_portgroup: "dvpg-db-prod",
          vlan: 122,
          target_vnet: "vnet-prod",
          target_subnet: "snet-db",
          security_intent: "Allow SQL traffic from app tier only.",
        },
      ],
      readiness: {
        blockers: 1,
        warnings: 1,
        findings: [
          {
            rule_id: "vmware.snapshot.exists",
            severity: "blocker",
            target_name: "claims-db-01",
            target_node_id: "vm:vm-103",
            message: "claims-db-01 has one or more VMware snapshots.",
          },
        ],
      },
      target_design: {
        vnet: "vnet-prod",
        subnets: ["snet-web", "snet-app", "snet-db"],
        vm_targets: [
          {
            name: "claims-db-01",
            vm_size: "Standard_D8s_v5",
            subnet: "snet-db",
            disk_type: "Premium SSD",
          },
        ],
      },
      artifact_href: "/artifacts/release1-assessment.md",
      artifacts: [
        {
          label: "Assessment summary",
          href: "/artifacts/release1-assessment.md",
          kind: "markdown",
        },
        {
          label: "Migration blueprint",
          href: "/artifacts/release1-blueprint.yaml",
          kind: "yaml",
        },
        {
          label: "Cutover runbook",
          href: "/artifacts/release1-runbook.md",
          kind: "markdown",
        },
        {
          label: "Terraform draft",
          href: "/artifacts/release1-main.tf",
          kind: "terraform",
        },
      ],
    };
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      const path = input.toString();

      if (path === "/workspace/release1-demo") {
        return Promise.resolve(new Response(JSON.stringify(workspaceResponse), { status: 200 }));
      }

      if (path === "/approvals/release1-demo" && init === undefined) {
        return Promise.resolve(new Response(JSON.stringify(workspaceResponse.workflow), { status: 200 }));
      }

      if (path === "/imports/vmware-fixture" && init?.method === "POST") {
        return Promise.resolve(
          new Response(JSON.stringify({ nodes: 12, edges: 13, persisted: true }), {
            status: 200,
          }),
        );
      }

      if (path === "/collectors/release1-demo/deploy" && init?.method === "POST") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              ...workspaceResponse.intake,
              collector: {
                ...workspaceResponse.intake.collector,
                status: "connected",
                last_heartbeat_at: "2026-05-10T12:00:00Z",
              },
            }),
            { status: 200 },
          ),
        );
      }

      if (path === "/discovery-runs/release1-demo/start" && init?.method === "POST") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              ...workspaceResponse.intake,
              collector: {
                ...workspaceResponse.intake.collector,
                status: "connected",
                last_heartbeat_at: "2026-05-10T12:00:00Z",
              },
              discovery: {
                run_id: "discovery-release1-demo-001",
                status: "completed",
                source: "fixture",
                compute_nodes: 3,
                network_segments: 3,
                graph_nodes: 12,
                graph_edges: 13,
                estimate_ready: true,
              },
            }),
            { status: 200 },
          ),
        );
      }

      if (
        path === "/approvals/release1-demo/commercial_estimate_approval/approve" &&
        init?.method === "POST"
      ) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              gate: "commercial_estimate_approval",
              status: "approved",
              actor: "consultant@example.com",
              reason: "Approved from Consultant Workspace.",
            }),
            { status: 200 },
          ),
        );
      }

      if (path === "/migration-waves/release1-demo" && init?.method === "POST") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              wave_id: "wave-001",
              status: "ready_for_test_migration",
              selected_compute_nodes: ["claims-db-01"],
              execution_backend: "azure-migrate",
              operation_count: 5,
              approval_gates: [
                "test_migration_approval",
                "source_shutdown_approval",
                "cutover_approval",
              ],
              ready_count: 0,
              blocked_count: 1,
              blockers: [
                {
                  name: "claims-db-01",
                  readiness: "Blocked",
                  message: "claims-db-01 has one or more VMware snapshots.",
                },
              ],
              next_action: "Resolve blockers before test migration.",
            }),
            { status: 200 },
          ),
        );
      }

      if (path === "/remediation-plans/release1-demo" && init?.method === "POST") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              plan_id: "remediation-wave-001",
              status: "consultant_review_required",
              task_count: 2,
              tasks: [
                {
                  task_id: "remediate-claims-db-01-vmware-snapshot-exists",
                  target_name: "claims-db-01",
                  rule_id: "vmware.snapshot.exists",
                  severity: "blocker",
                  owner_role: "VMware administrator",
                  automation_mode: "human_approved_manual_step",
                  approval_required: true,
                  recommended_action:
                    "Consolidate or remove VMware snapshots before replication.",
                },
                {
                  task_id: "remediate-claims-db-01-vmware-tools-outdated",
                  target_name: "claims-db-01",
                  rule_id: "vmware.tools.outdated",
                  severity: "warning",
                  owner_role: "VMware administrator",
                  automation_mode: "human_approved_manual_step",
                  approval_required: false,
                  recommended_action:
                    "Repair or update VMware Tools before relying on guest metadata.",
                },
              ],
              next_action: "Assign remediation tasks before test migration.",
            }),
            { status: 200 },
          ),
        );
      }

      return Promise.resolve(new Response("Not found", { status: 404 }));
    });

    render(<App />);

    expect(
      await screen.findByRole("heading", { name: "Claims Portal" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "OmniBridge Consultant Workspace" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "VMware ingress" })).toBeInTheDocument();
    expect(screen.getByText("Collector not deployed")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Cost estimate" })).toBeInTheDocument();
    expect(screen.getByText("Locked until discovery")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Migration scope" })).toBeInTheDocument();
    expect(screen.getByText("Locked until estimate approval")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Deploy collector" }));
    expect(await screen.findByText("Connected to vcsa-prod-01")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Run data collection" }));
    expect(await screen.findByText("Discovery complete")).toBeInTheDocument();
    expect(screen.getByText("3 VMs discovered")).toBeInTheDocument();
    expect(screen.getByText("$27,250 project fee")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Approve estimate package" }));
    expect(await screen.findByText("5 pending")).toBeInTheDocument();
    expect(screen.getByText("Estimate approved")).toBeInTheDocument();
    expect(screen.getByText("1 VM selected for wave-001")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Create migration wave" }));
    expect(await screen.findByText("Wave wave-001 staged")).toBeInTheDocument();
    expect(screen.getByText("Wave created")).toBeInTheDocument();
    expect(screen.getByText("Resolve blockers before test migration.")).toBeInTheDocument();
    expect(await screen.findByText("Remediation plan generated")).toBeInTheDocument();
    expect(
      screen.getByText("Consolidate or remove VMware snapshots before replication."),
    ).toBeInTheDocument();
    expect(screen.getAllByText("5").length).toBeGreaterThan(0);
    expect(screen.getByText("$27,250")).toBeInTheDocument();
    expect(screen.getAllByText("$1,800").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: "Estimate breakdown" })).toBeInTheDocument();
    expect(screen.getByText("assessment_base")).toBeInTheDocument();
    expect(screen.getByText("compute_node_assessment")).toBeInTheDocument();
    expect(screen.getByText("9,000,000 tokens")).toBeInTheDocument();
    expect(screen.getByText("$0.20 / 1k tokens")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Approval ledger" })).toBeInTheDocument();
    expect(screen.getByText("BLUEPRINT_GENERATED")).toBeInTheDocument();
    expect(screen.getByText("commercial_estimate_approval")).toBeInTheDocument();
    expect(screen.getByText("approved")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Azure Migrate execution plan" })).toBeInTheDocument();
    expect(screen.getAllByText("dry_run").length).toBeGreaterThan(0);
    expect(screen.getByText("start_test_migration")).toBeInTheDocument();
    expect(screen.getAllByText("test_migration_approval").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: "Validation evidence" })).toBeInTheDocument();
    expect(screen.getByText("18 checks")).toBeInTheDocument();
    expect(screen.getAllByText("vm_boot").length).toBeGreaterThan(0);
    expect(
      screen.getByText("Resolve preflight blockers before test migration."),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Canonical graph" })).toBeInTheDocument();
    expect(screen.getByText("ComputeNode: 3")).toBeInTheDocument();
    expect(screen.getByText("RUNS_ON")).toBeInTheDocument();
    expect(screen.getByText("HAS_VOLUME")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Graph persistence" })).toBeInTheDocument();
    expect(screen.getByText("12 nodes / 13 edges")).toBeInTheDocument();
    expect(screen.getAllByText("Neo4j not configured").length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "Persist to Neo4j" }));
    expect(await screen.findByText("Persisted to Neo4j")).toBeInTheDocument();
    expect(screen.getByText("Confirm whether claims-db-01 snapshot can be removed.")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Estate inventory" })).toBeInTheDocument();
    expect(screen.getAllByText("claims-db-01").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Standard_D8s_v5").length).toBeGreaterThan(0);
    expect(screen.getByText("dvpg-db-prod")).toBeInTheDocument();
    expect(screen.getAllByText((content) => content.includes("snet-db")).length).toBeGreaterThan(0);
    expect(screen.getByText("vmware.snapshot.exists")).toBeInTheDocument();
    expect(screen.getByText("source_shutdown_approval")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Migration blueprint yaml" })).toHaveAttribute(
      "href",
      "/artifacts/release1-blueprint.yaml",
    );
    expect(screen.getByRole("link", { name: "Cutover runbook markdown" })).toHaveAttribute(
      "href",
      "/artifacts/release1-runbook.md",
    );
    expect(screen.getByRole("link", { name: "Terraform draft terraform" })).toHaveAttribute(
      "href",
      "/artifacts/release1-main.tf",
    );

    expect(fetchMock).toHaveBeenCalledWith("/workspace/release1-demo");
    expect(fetchMock).toHaveBeenCalledWith("/approvals/release1-demo");
    expect(fetchMock).toHaveBeenCalledWith(
      "/collectors/release1-demo/deploy",
      expect.objectContaining({ method: "POST" }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/discovery-runs/release1-demo/start",
      expect.objectContaining({ method: "POST" }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/migration-waves/release1-demo",
      expect.objectContaining({ method: "POST" }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/remediation-plans/release1-demo",
      expect.objectContaining({ method: "POST" }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/imports/vmware-fixture",
      expect.objectContaining({ method: "POST" }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/approvals/release1-demo/commercial_estimate_approval/approve",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("shows a recoverable error when the workspace API cannot be loaded", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("Unavailable", { status: 503 }));

    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Unable to load workspace data.",
    );
  });
});
