"""MCP STDIO server exposing Google Calendar v3 operations."""

from __future__ import annotations

from typing import Any

from googleapiclient.discovery import build
from mcp.server.fastmcp import FastMCP

from gcal_mcp.auth import load_credentials

mcp = FastMCP("gcal-local")


def _service():
    """Build a Calendar v3 service for each call. Cheap (no network)."""
    return build(
        "calendar", "v3", credentials=load_credentials(), cache_discovery=False
    )


@mcp.tool()
def list_calendars() -> list[dict[str, Any]]:
    """List all calendars accessible to the authenticated user."""
    items = _service().calendarList().list().execute().get("items", [])
    return [
        {
            "id": c["id"],
            "summary": c.get("summary"),
            "timeZone": c.get("timeZone"),
            "primary": c.get("primary", False),
            "accessRole": c.get("accessRole"),
            "backgroundColor": c.get("backgroundColor"),
        }
        for c in items
    ]


@mcp.tool()
def list_events(
    calendar_id: str = "primary",
    time_min: str | None = None,
    time_max: str | None = None,
    q: str | None = None,
    max_results: int = 50,
) -> list[dict[str, Any]]:
    """List events from a calendar, ordered by start time.

    Args:
        calendar_id: Calendar ID. Default 'primary'.
        time_min: ISO 8601 lower bound (inclusive). Optional.
        time_max: ISO 8601 upper bound (exclusive). Optional.
        q: Free-text search query. Optional.
        max_results: Max events to return. Default 50.
    """
    kwargs: dict[str, Any] = {
        "calendarId": calendar_id,
        "maxResults": max_results,
        "singleEvents": True,
        "orderBy": "startTime",
    }
    if time_min:
        kwargs["timeMin"] = time_min
    if time_max:
        kwargs["timeMax"] = time_max
    if q:
        kwargs["q"] = q
    return _service().events().list(**kwargs).execute().get("items", [])


@mcp.tool()
def get_event(event_id: str, calendar_id: str = "primary") -> dict[str, Any]:
    """Get a single event by ID."""
    return (
        _service().events().get(calendarId=calendar_id, eventId=event_id).execute()
    )


@mcp.tool()
def create_event(
    summary: str,
    start: str,
    end: str,
    calendar_id: str = "primary",
    time_zone: str | None = None,
    description: str | None = None,
    location: str | None = None,
    attendees: list[str] | None = None,
    all_day: bool = False,
    reminders_overrides: list[dict[str, Any]] | None = None,
    use_default_reminders: bool = True,
    color_id: str | None = None,
    extended_properties_private: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Create a calendar event.

    Args:
        summary: Event title (required).
        start: ISO 8601 datetime, or 'YYYY-MM-DD' if all_day.
        end: ISO 8601 datetime, or 'YYYY-MM-DD' (next day) if all_day.
        calendar_id: Calendar ID. Default 'primary'.
        time_zone: IANA timezone (e.g. 'Asia/Taipei'). Optional.
        description: Free text. Optional.
        location: Free text. Optional.
        attendees: List of email addresses. Optional.
        all_day: If True, start/end are dates without time.
        reminders_overrides: List of {method: 'popup'|'email', minutes: int}.
            When provided, automatically sets useDefault=False unless
            use_default_reminders is also explicitly True.
        use_default_reminders: If True (default), inherit calendar defaults.
            Set to False to suppress all reminders or to apply only the
            given overrides.
        color_id: '1'-'11' referring to event color palette. Optional.
        extended_properties_private: Custom private metadata, e.g. for
            sync-tool reverse pointers like {'todoSourceId': 'abc123'}.
    """
    body: dict[str, Any] = {"summary": summary}
    if all_day:
        body["start"] = {"date": start}
        body["end"] = {"date": end}
    else:
        body["start"] = {"dateTime": start}
        body["end"] = {"dateTime": end}
        if time_zone:
            body["start"]["timeZone"] = time_zone
            body["end"]["timeZone"] = time_zone
    if description:
        body["description"] = description
    if location:
        body["location"] = location
    if attendees:
        body["attendees"] = [{"email": e} for e in attendees]
    if color_id:
        body["colorId"] = color_id
    if extended_properties_private:
        body["extendedProperties"] = {"private": extended_properties_private}

    if reminders_overrides is not None:
        body["reminders"] = {
            "useDefault": False,
            "overrides": reminders_overrides,
        }
    elif not use_default_reminders:
        body["reminders"] = {"useDefault": False}

    return (
        _service()
        .events()
        .insert(calendarId=calendar_id, body=body)
        .execute()
    )


@mcp.tool()
def update_event(
    event_id: str,
    calendar_id: str = "primary",
    summary: str | None = None,
    start: str | None = None,
    end: str | None = None,
    time_zone: str | None = None,
    description: str | None = None,
    location: str | None = None,
    reminders_overrides: list[dict[str, Any]] | None = None,
    use_default_reminders: bool | None = None,
    color_id: str | None = None,
    extended_properties_private: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Patch an existing event. Only fields explicitly passed are updated."""
    body: dict[str, Any] = {}
    if summary is not None:
        body["summary"] = summary
    if start is not None:
        body["start"] = {"dateTime": start}
        if time_zone:
            body["start"]["timeZone"] = time_zone
    if end is not None:
        body["end"] = {"dateTime": end}
        if time_zone:
            body["end"]["timeZone"] = time_zone
    if description is not None:
        body["description"] = description
    if location is not None:
        body["location"] = location
    if color_id is not None:
        body["colorId"] = color_id
    if extended_properties_private is not None:
        body["extendedProperties"] = {"private": extended_properties_private}

    if use_default_reminders is not None or reminders_overrides is not None:
        reminders: dict[str, Any] = {}
        if use_default_reminders is not None:
            reminders["useDefault"] = use_default_reminders
        if reminders_overrides is not None:
            reminders["overrides"] = reminders_overrides
            if "useDefault" not in reminders:
                reminders["useDefault"] = False
        body["reminders"] = reminders

    return (
        _service()
        .events()
        .patch(calendarId=calendar_id, eventId=event_id, body=body)
        .execute()
    )


@mcp.tool()
def delete_event(
    event_id: str, calendar_id: str = "primary"
) -> dict[str, str]:
    """Delete an event by ID."""
    _service().events().delete(
        calendarId=calendar_id, eventId=event_id
    ).execute()
    return {
        "status": "deleted",
        "event_id": event_id,
        "calendar_id": calendar_id,
    }


# --------------------------------------------------------------------------
# Google Tasks v1
#
# The Tasks API records only the DATE part of `due` — the time is discarded on
# write and is not readable, even though the mobile app can set one. Anything
# needing a time-of-day reminder belongs in a calendar event, not a task.
# --------------------------------------------------------------------------


def _tasks_service():
    """Build a Tasks v1 service for each call. Cheap (no network)."""
    return build(
        "tasks", "v1", credentials=load_credentials(), cache_discovery=False
    )


def _rfc3339_due(due: str) -> str:
    """Normalise a due date to the RFC 3339 form the Tasks API expects."""
    return f"{due}T00:00:00.000Z" if len(due) == 10 else due


@mcp.tool()
def list_task_lists() -> list[dict[str, Any]]:
    """List all Google Tasks lists (the 'boards' tasks are filed under)."""
    items = _tasks_service().tasklists().list(maxResults=100).execute()
    return [
        {"id": t["id"], "title": t.get("title"), "updated": t.get("updated")}
        for t in items.get("items", [])
    ]


@mcp.tool()
def list_tasks(
    task_list_id: str = "@default",
    show_completed: bool = False,
    due_min: str | None = None,
    due_max: str | None = None,
    max_results: int = 100,
) -> list[dict[str, Any]]:
    """List tasks in a list, in the user's manual (drag) order.

    Args:
        task_list_id: Task list ID from list_task_lists. Default '@default'.
        show_completed: Include completed tasks. Default False.
        due_min: 'YYYY-MM-DD' lower bound on due date. Optional.
        due_max: 'YYYY-MM-DD' upper bound on due date. Optional.
        max_results: Max tasks to return. Default 100.
    """
    kwargs: dict[str, Any] = {
        "tasklist": task_list_id,
        "maxResults": max_results,
        "showCompleted": show_completed,
        # Completed tasks are also flagged hidden, so showCompleted alone
        # returns nothing without this.
        "showHidden": show_completed,
    }
    if due_min:
        kwargs["dueMin"] = _rfc3339_due(due_min)
    if due_max:
        kwargs["dueMax"] = _rfc3339_due(due_max)
    items = _tasks_service().tasks().list(**kwargs).execute().get("items", [])
    return [
        {
            "id": t["id"],
            "title": t.get("title"),
            "status": t.get("status"),
            "due": (t.get("due") or "")[:10],
            "notes": t.get("notes"),
            "parent": t.get("parent"),
            "position": t.get("position"),
        }
        for t in items
    ]


@mcp.tool()
def create_task(
    title: str,
    task_list_id: str = "@default",
    notes: str | None = None,
    due: str | None = None,
    parent: str | None = None,
) -> dict[str, Any]:
    """Create a task.

    Args:
        title: Task title (required).
        task_list_id: Task list ID. Default '@default'.
        notes: Free-text body. Optional.
        due: Due date as 'YYYY-MM-DD'. Time of day is not supported by the
            API — use create_event for anything needing a timed reminder.
        parent: Parent task ID to nest under. Optional.
    """
    body: dict[str, Any] = {"title": title}
    if notes:
        body["notes"] = notes
    if due:
        body["due"] = _rfc3339_due(due)
    kwargs: dict[str, Any] = {"tasklist": task_list_id, "body": body}
    if parent:
        kwargs["parent"] = parent
    return _tasks_service().tasks().insert(**kwargs).execute()


def _task_patch_body(
    title: str | None, notes: str | None, due: str | None, clear_due: bool
) -> dict[str, Any]:
    """Build the patch body for update_task. Omitted fields stay untouched.

    An explicit None `due` cannot double as "clear it" — that is what the
    caller sends when they only mean to edit the title — so clearing needs
    its own flag.
    """
    body: dict[str, Any] = {}
    if title is not None:
        body["title"] = title
    if notes is not None:
        body["notes"] = notes
    if clear_due:
        body["due"] = None
    elif due:
        body["due"] = _rfc3339_due(due)
    return body


@mcp.tool()
def update_task(
    task_id: str,
    task_list_id: str = "@default",
    title: str | None = None,
    notes: str | None = None,
    due: str | None = None,
    clear_due: bool = False,
) -> dict[str, Any]:
    """Edit a task in place. Only the fields you pass are changed.

    Use this to reschedule or reword an existing task instead of
    completing and recreating it — recreating a parent task orphans its
    subtasks, and recreating anything loses its manual list position.

    Args:
        task_id: Task ID from list_tasks.
        task_list_id: Task list ID. Default '@default'.
        notes: Replacement notes body. Replaces the old one wholesale, so
            pass the full text, not just the part you are adding.
        due: New due date as 'YYYY-MM-DD'. Time of day is not supported by
            the API — use create_event for anything needing a timed reminder.
        clear_due: Remove the due date entirely. Wins over `due`.

    Does not move a task between lists or reparent it; the API needs a
    separate move call for that.
    """
    body = _task_patch_body(title, notes, due, clear_due)
    if not body:
        raise ValueError(
            "update_task needs at least one of title / notes / due / clear_due"
        )
    return (
        _tasks_service()
        .tasks()
        .patch(tasklist=task_list_id, task=task_id, body=body)
        .execute()
    )


@mcp.tool()
def complete_task(
    task_id: str, task_list_id: str = "@default"
) -> dict[str, Any]:
    """Mark a task completed."""
    return (
        _tasks_service()
        .tasks()
        .patch(
            tasklist=task_list_id, task=task_id, body={"status": "completed"}
        )
        .execute()
    )


@mcp.tool()
def delete_task(task_id: str, task_list_id: str = "@default") -> dict[str, str]:
    """Delete a task by ID."""
    _tasks_service().tasks().delete(
        tasklist=task_list_id, task=task_id
    ).execute()
    return {
        "status": "deleted",
        "task_id": task_id,
        "task_list_id": task_list_id,
    }


def run_server() -> None:
    """Entry point used by python -m gcal_mcp."""
    mcp.run()
