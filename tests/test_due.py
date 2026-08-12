"""Self-check for the pure logic in the Tasks tools and the scope guard.

Run inside the image:
    docker run --rm --entrypoint python -v "$PWD/tests:/app/tests" \
        gcal-mcp:latest -m tests.test_due
"""

from gcal_mcp.auth import SCOPES, missing_scopes
from gcal_mcp.server import _rfc3339_due

# --- due-date normalisation ---

# Bare dates get the midnight-UTC suffix the API requires.
assert _rfc3339_due("2026-08-12") == "2026-08-12T00:00:00.000Z"

# Already-RFC3339 values pass through untouched (the API discards the time
# either way, so there is nothing to normalise).
assert _rfc3339_due("2026-08-12T09:30:00.000Z") == "2026-08-12T09:30:00.000Z"

# --- scope guard ---

CAL = "https://www.googleapis.com/auth/calendar"
TASKS = "https://www.googleapis.com/auth/tasks"

# A pre-Tasks token: the guard must catch it. This is the whole point — the
# real failure it prevents is an opaque `invalid_scope` raised from refresh.
assert missing_scopes([CAL]) == [TASKS]

# A token carrying everything, in any order, passes.
assert missing_scopes(list(reversed(SCOPES))) == []

# Extra scopes beyond ours are fine; a missing `scopes` key means nothing.
assert missing_scopes(SCOPES + ["https://example.test/other"]) == []
assert missing_scopes(None) == sorted(SCOPES)

print("ok")
