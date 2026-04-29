"""OAuth credential loading + interactive auth flow.

Token files live in the directory pointed to by `GCAL_MCP_CONFIG_DIR`
(defaults to `~/.config/gcal-mcp`). Inside the Docker image this is bind-
mounted to `/config`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES: list[str] = [
    "https://www.googleapis.com/auth/calendar",
]


def config_dir() -> Path:
    return Path(
        os.environ.get(
            "GCAL_MCP_CONFIG_DIR", str(Path.home() / ".config" / "gcal-mcp")
        )
    )


def client_secret_path() -> Path:
    return config_dir() / "client_secret.json"


def token_path() -> Path:
    return config_dir() / "token.json"


def load_credentials() -> Credentials:
    """Load credentials, refreshing if expired.

    Raises RuntimeError if no token exists or refresh fails — in that case the
    caller (or user) must run `auth.sh` to perform the interactive OAuth flow.
    """
    tp = token_path()
    if not tp.exists():
        raise RuntimeError(
            f"No token at {tp}. Run `./auth.sh` once to perform initial OAuth."
        )
    creds = Credentials.from_authorized_user_file(str(tp), SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            tp.write_text(creds.to_json())
            tp.chmod(0o600)
        else:
            raise RuntimeError(
                "Credentials invalid and cannot refresh; re-run ./auth.sh."
            )
    return creds


def run_auth_flow() -> None:
    """Run the interactive OAuth flow.

    Binds a local server on 0.0.0.0:8080 inside the container so the host's
    `-p 8080:8080` port forward can reach the redirect URI. The user opens
    the printed URL in their host browser, consents, and Google redirects to
    `http://localhost:8080/?code=...` which the local server captures.
    """
    cs = client_secret_path()
    tp = token_path()
    if not cs.exists():
        print(f"ERROR: client_secret.json not found at {cs}", file=sys.stderr)
        raise SystemExit(1)

    print(
        "[gcal-mcp] starting OAuth flow. The URL printed below should be "
        "opened in your host browser.",
        flush=True,
    )
    flow = InstalledAppFlow.from_client_secrets_file(str(cs), SCOPES)
    # Google OAuth rejects 0.0.0.0 as a redirect URI host (only 'localhost'
    # and '127.0.0.1' are accepted for loopback). We need to bind the socket
    # to 0.0.0.0 inside the container (so the host's `-p 8080:8080` forward
    # can reach us) but advertise 'localhost' to Google as the redirect URI.
    creds = flow.run_local_server(
        host="localhost",
        bind_addr="0.0.0.0",
        port=8080,
        open_browser=False,
    )
    tp.write_text(creds.to_json())
    tp.chmod(0o600)
    print(f"[gcal-mcp] token saved to {tp}", flush=True)
