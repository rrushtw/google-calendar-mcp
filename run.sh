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

# 給容器一個對得上 session 的名字，取代 Docker 隨機名。
# 命名：gcal-mcp-<專案目錄名>-<session 前 8 碼>
# 目錄名讓人一眼認出是哪個專案；session id 後綴保證同目錄多 session 不撞名。
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
DIR_SLUG="$(basename "$PROJECT_DIR" | tr -c 'a-zA-Z0-9_.-' '-' | sed 's/--*/-/g; s/^-//; s/-$//')"
SID="${CLAUDE_CODE_SESSION_ID:-nosession}"
CONTAINER_NAME="gcal-mcp-${DIR_SLUG:-unknown}-${SID:0:8}"

# 若同名孤兒容器殘留（前一個 session 被強制砍掉而沒清乾淨）先移除，避免 --name 撞名失敗。
docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true

exec docker run -i --rm \
  --name "$CONTAINER_NAME" \
  --user "$(id -u):$(id -g)" \
  -v "$CONFIG_DIR:/config" \
  "$IMAGE_TAG"
