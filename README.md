# OmniBridge

OmniBridge is an AI-assisted migration factory for moving enterprise technology estates from one operating environment to another.

The platform discovers source environments, builds a canonical technology graph, generates priced migration blueprints, and executes approved migration workflows through deterministic engines.

VMware-to-Azure is the first migration corridor, not the whole product.

## Repository Layout

```text
docs/
  PRODUCT_SPEC.md
  CORRIDOR_CONTRACT.md

corridors/
  vmware-to-azure/
    corridor.yaml
    README.md
```

Future platform code should keep these boundaries:

- `apps/` for deployable applications such as the web UI, API, and on-prem appliance.
- `packages/` for shared platform engines such as the canonical graph, estimator, rules engine, workflow engine, and agent tools.
- `connectors/` for platform API access such as VMware vCenter, Azure Resource Manager, and Azure Migrate.
- `corridors/` for source-to-target migration packages such as VMware-to-Azure, VMware-to-AWS, or AWS-to-Azure.

## Start Here

- [docs/PRODUCT_SPEC.md](docs/PRODUCT_SPEC.md)
- [docs/CORRIDOR_CONTRACT.md](docs/CORRIDOR_CONTRACT.md)
- [corridors/vmware-to-azure/README.md](corridors/vmware-to-azure/README.md)

