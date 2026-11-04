#!/usr/bin/env bash
set -euo pipefail

uv run pytest
pnpm -C apps/web test
pnpm -C apps/web build
docker compose config >/dev/null
