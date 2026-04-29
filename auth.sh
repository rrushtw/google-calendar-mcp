#!/usr/bin/env bash
# One-time interactive OAuth flow.
# Opens a localhost:8080 server inside the container; the user clicks the
# printed URL in their host browser to consent.

set -euo pipefail

IMAGE_TAG="gcal-mcp:latest"
CONFIG_DIR="${HOME}/.config/gcal-mcp"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! docker image inspect "$IMAGE_TAG" >/dev/null 2>&1; then
  echo "[gcal-mcp] image not found, building..." >&2
  docker build -t "$IMAGE_TAG" "$SCRIPT_DIR" >&2
fi

if [[ ! -f "$CONFIG_DIR/client_secret.json" ]]; then
  echo "ERROR: $CONFIG_DIR/client_secret.json not found." >&2
  echo "       Place your GCP Desktop-type OAuth client JSON there first." >&2
  exit 1
fi

echo "[gcal-mcp] starting OAuth flow on host port 8080..." >&2
echo "[gcal-mcp] copy the URL printed below into your host browser." >&2
exec docker run -it --rm \
  --user "$(id -u):$(id -g)" \
  -p 8080:8080 \
  -v "$CONFIG_DIR:/config" \
  "$IMAGE_TAG" \
  --auth
