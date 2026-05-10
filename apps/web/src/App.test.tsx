// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";

import { cleanup, render, screen } from "@testing-library/react";
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
      ],
    };
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const path = input.toString();

      if (path !== "/workspace/release1-demo") {
        return Promise.resolve(new Response("Not found", { status: 404 }));
      }

      return Promise.resolve(new Response(JSON.stringify(workspaceResponse), { status: 200 }));
    });

    render(<App />);

    expect(
      await screen.findByRole("heading", { name: "Claims Portal" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "OmniBridge Consultant Workspace" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Approve Estimate" })).toBeInTheDocument();
    expect(screen.getByText("$27,250")).toBeInTheDocument();
    expect(screen.getAllByText("$1,800").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: "Estimate breakdown" })).toBeInTheDocument();
    expect(screen.getByText("assessment_base")).toBeInTheDocument();
    expect(screen.getByText("compute_node_assessment")).toBeInTheDocument();
    expect(screen.getByText("9,000,000 tokens")).toBeInTheDocument();
    expect(screen.getByText("$0.20 / 1k tokens")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Canonical graph" })).toBeInTheDocument();
    expect(screen.getByText("ComputeNode: 3")).toBeInTheDocument();
    expect(screen.getByText("RUNS_ON")).toBeInTheDocument();
    expect(screen.getByText("HAS_VOLUME")).toBeInTheDocument();
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

    expect(fetchMock).toHaveBeenCalledWith("/workspace/release1-demo");
  });

  it("shows a recoverable error when the workspace API cannot be loaded", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("Unavailable", { status: 503 }));

    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Unable to load workspace data.",
    );
  });
});
