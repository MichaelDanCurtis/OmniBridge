# VMware-to-Azure Corridor

This corridor is the first OmniBridge migration package.

It maps VMware vCenter estates into the OmniBridge canonical technology graph, projects selected workloads into Azure target designs, estimates project cost and effort, generates migration blueprints, and prepares execution through Azure Migrate where supported.

## Corridor Role

This package owns VMware-to-Azure migration knowledge:

- VMware inventory interpretation
- VMware object to canonical graph mapping
- VMware network to Azure network projection
- VMware VM to Azure VM target design
- VMware readiness rules
- Azure Migrate execution mapping
- VMware-to-Azure estimate multipliers
- VMware-to-Azure deliverable templates

The platform owns shared factory services:

- project lifecycle
- canonical graph storage
- estimator runtime
- workflow engine
- approval model
- audit trail
- agent runtime
- UI shell

## Release 1 Focus

Release 1 should prioritize:

- read-only vCenter discovery
- import-based assessment fixtures
- canonical mapping for VMs, disks, NICs, datastores, clusters, hosts, port groups, and vApps
- Azure target design recommendations
- readiness analysis
- cost and effort estimation
- migration blueprint generation
- SOW and assessment deliverables
- Azure Migrate workflow mapping

Release 1 should not own powered-on custom replication or a full VDDK conversion engine.

