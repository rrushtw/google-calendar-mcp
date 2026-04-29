#!/usr/bin/env bash
# Spawned by Claude Code as the MCP STDIO transport.
# stdin/stdout are piped to/from the Claude Code process.

set -euo pipefail

IMAGE_TAG="gcal-mcp:latest"
CONFIG_DIR="${HOME}/.config/gcal-mcp"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! docker image inspect "$IMAGE_TAG" >/dev/null 2>&1; then
  echo "[gcal-mcp] image not found, building..." >&2
  docker build -t "$IMAGE_TAG" "$SCRIPT_DIR" >&2
fi

if [[ ! -f "$CONFIG_DIR/token.json" ]]; then
  echo "ERROR: $CONFIG_DIR/token.json not found. Run ./auth.sh first." >&2
  exit 1
fi

exec docker run -i --rm \
  --user "$(id -u):$(id -g)" \
  -v "$CONFIG_DIR:/config" \
  "$IMAGE_TAG"
