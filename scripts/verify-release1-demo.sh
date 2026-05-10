#!/usr/bin/env bash
set -euo pipefail

uv run pytest
pnpm -C apps/web test
docker compose config >/dev/null
