"""Self-check for the pure logic in the Tasks tools and the scope guard.

Run inside the image:
    docker run --rm --entrypoint python -v "$PWD/tests:/app/tests" \
        gcal-mcp:latest -m tests.test_due
"""

from gcal_mcp.auth import SCOPES, missing_scopes
from gcal_mcp.server import _rfc3339_due, _task_patch_body

# --- due-date normalisation ---

# Bare dates get the midnight-UTC suffix the API requires.
assert _rfc3339_due("2026-08-12") == "2026-08-12T00:00:00.000Z"

# Already-RFC3339 values pass through untouched (the API discards the time
# either way, so there is nothing to normalise).
assert _rfc3339_due("2026-08-12T09:30:00.000Z") == "2026-08-12T09:30:00.000Z"

# --- update_task patch body ---

# Only what was passed appears, so a title edit cannot wipe the notes.
assert _task_patch_body("new", None, None, False) == {"title": "new"}

# A due date is normalised on the way in, same as create_task.
assert _task_patch_body(None, None, "2026-08-31", False) == {
    "due": "2026-08-31T00:00:00.000Z"
}

# Clearing sends an explicit null; that is the only way the API drops a due
# date, and it must not be confused with "field not given".
assert _task_patch_body(None, None, None, True) == {"due": None}

# clear_due wins over a supplied date rather than silently picking one.
assert _task_patch_body(None, None, "2026-08-31", True) == {"due": None}

# Empty notes are a legitimate edit (wiping the body), unlike None.
assert _task_patch_body(None, "", None, False) == {"notes": ""}

# Nothing passed yields an empty body — update_task turns this into an error
# rather than issuing a no-op PATCH.
assert _task_patch_body(None, None, None, False) == {}

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
