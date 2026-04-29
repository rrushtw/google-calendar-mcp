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


def run_server() -> None:
    """Entry point used by python -m gcal_mcp."""
    mcp.run()
