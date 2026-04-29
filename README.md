# google-calendar-mcp

Local-only MCP server for Google Calendar. Runs as a Docker STDIO server
spawned by Claude Code. OAuth tokens stay on your machine; nothing transits
through claude.ai or any third party.

## Why local-only

Claude Code's claude.ai-managed MCP connectors are scoped to the
claude.ai account. If that account is shared (e.g., a team account), enabling
a connector exposes data to every account user. This server runs entirely on
your machine with credentials you control.

## Prerequisites

- Docker (any recent version)
- A GCP **OAuth 2.0 Client ID — Desktop app type** with the Google Calendar
  API enabled
- `client_secret.json` placed at `~/.config/gcal-mcp/client_secret.json`
  (`chmod 600`)
- Host port 8080 free during the one-time auth step

## First-run setup

1. Place `client_secret.json` at `~/.config/gcal-mcp/`:

   ```bash
   mkdir -p ~/.config/gcal-mcp
   chmod 700 ~/.config/gcal-mcp
   cp /path/to/client_secret_xxx.json ~/.config/gcal-mcp/client_secret.json
   chmod 600 ~/.config/gcal-mcp/client_secret.json
   ```

2. Run the auth flow:

   ```bash
   ./auth.sh
   ```

   First run builds the Docker image (~200MB). Then the script prints a URL.
   Open it in your host browser, consent to the requested scopes
   (`https://www.googleapis.com/auth/calendar`). On success, the script
   writes `~/.config/gcal-mcp/token.json` and exits.

3. (Optional) Sanity check:

   ```bash
   echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | ./run.sh
   ```

   You should see a JSON-RPC response listing the tools below.

## Wire into Claude Code

Add to `~/.claude/settings.json` (**user scope** — not project-scope
`.mcp.json`, to keep this off any repo you share):

```json
{
  "mcpServers": {
    "gcal-local": {
      "command": "/home/<you>/claude/google-calendar-mcp/run.sh",
      "args": []
    }
  }
}
```

Restart Claude Code. New sessions will spawn the server on demand.

## Tools exposed

| Tool | Purpose |
|---|---|
| `list_calendars` | Enumerate all writable calendars. |
| `list_events` | List events in a calendar; supports `time_min` / `time_max` / `q`. |
| `get_event` | Fetch one event by ID. |
| `create_event` | Insert event. Supports `reminders_overrides` for per-event multi-layer popups (the claude.ai connector did *not* expose this). |
| `update_event` | Patch existing event. Only provided fields are updated. |
| `delete_event` | Delete by ID. |

## Token refresh

`google-auth` automatically refreshes the access token using the stored
refresh token. The refreshed `token.json` is written back to disk. If the
refresh token is revoked or its 6-month inactivity window elapses,
re-run `./auth.sh`.

## Threat model

- `client_secret.json` and `token.json` live only at `~/.config/gcal-mcp/`
  on this machine. Bind-mounted into the container at `/config`.
- The container has no inbound network exposure during normal operation —
  only outbound HTTPS to `googleapis.com`. `auth.sh` temporarily exposes
  port 8080 for the OAuth callback.
- Container runs as root by default — acceptable since it's user-spawned and
  not network-reachable. Tighten with `--user` if desired.

## Layout

```
.
├── Dockerfile            # python:3.12-slim + deps
├── requirements.txt
├── auth.sh               # one-time interactive OAuth
├── run.sh                # Claude Code MCP entrypoint
├── gcal_mcp/
│   ├── __main__.py       # entry: default → server, --auth → OAuth flow
│   ├── auth.py           # credential load + InstalledAppFlow
│   └── server.py         # FastMCP server with @tool decorators
└── README.md
```
