"""Entry point. Default: run MCP STDIO server. With --auth: interactive OAuth flow."""

from __future__ import annotations

import sys


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--auth":
        from gcal_mcp.auth import run_auth_flow

        run_auth_flow()
        return
    from gcal_mcp.server import run_server

    run_server()


if __name__ == "__main__":
    main()
