# Connectors

Reusable source and target platform connectors live here.

Connectors own API access to a platform. They should not own source-to-target migration logic.

Expected initial connectors:

- `vmware-vcenter`: read-only VMware inventory and topology collection.
- `azure-arm`: Azure Resource Manager metadata and target resource operations.
- `azure-migrate`: Azure Migrate project and workflow integration.

