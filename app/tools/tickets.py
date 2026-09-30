from typing import Literal

from mcp.server.mcpserver import Context

from app.auth import get_auth_headers
from app.clients import work
from app.exception_handlers import tool_errors
from app.mcp_server import mcp

TicketType = Literal["epic", "bug", "feature", "task", "improvement"]
Priority = Literal["low", "medium", "high", "critical"]
Status = Literal["backlog", "todo", "in_progress", "in_review", "done"]


@mcp.tool()
@tool_errors
async def list_teams(ctx: Context, limit: int = 50, offset: int = 0) -> dict:
    """List the DevBoard teams the current user belongs to.

    Returns count, limit, offset and results. Use a team's id with list_projects.
    """
    return await work.list_teams(get_auth_headers(ctx), limit, offset)


@mcp.tool()
@tool_errors
async def list_projects(
    team_id: str, ctx: Context, limit: int = 50, offset: int = 0
) -> dict:
    """List the projects in a team.

    team_id is a team id from list_teams. Use a project's id with list tickets.
    """
    return await work.list_projects(team_id, get_auth_headers(ctx), limit, offset)


@mcp.tool()
@tool_errors
async def list_tickets(
    team_id: str, project_id: str, ctx: Context, limit: int = 50, offset: int = 0
) -> dict:
    """List the tickets in a project.

    team_id comes from list_teams and project_id from list_projects.
    """
    return await work.list_tickets(
        team_id, project_id, get_auth_headers(ctx), limit, offset
    )


@mcp.tool()
@tool_errors
async def get_ticket(team_id: str, project_id: str, ticket: str, ctx: Context) -> dict:
    """Get one ticket with full details (description, labels, dates).

    ticket is a ticket key like DB-67 or the ticket's id.
    """
    headers = get_auth_headers(ctx)
    ticket_id = await work.resolve_ticket_id(team_id, project_id, ticket, headers)
    return await work.get_ticket(team_id, project_id, ticket_id, headers)


@mcp.tool()
@tool_errors
async def create_ticket(
    team_id: str,
    project_id: str,
    title: str,
    type: TicketType,
    ctx: Context,
    description: str = "",
    priority: Priority = "medium",
    status: Status = "backlog",
    assignee_id: str | None = None,
    story_points: int | None = None,
    due_date: str | None = None,
) -> dict:
    """Create a ticket in a project.

    story_points must be a Fibonacci number (1, 2, 3, 5, 8, 13, 21).
    due_date is YYYY-MM-DD. Assigning someone other than yourself
    needs the Project Lead role.
    """
    body: dict = {
        "title": title,
        "type": type,
        "description": description,
        "priority": priority,
        "status": status,
    }
    if assignee_id is not None:
        body["assignee_id"] = assignee_id
    if story_points is not None:
        body["story_points"] = story_points
    if due_date is not None:
        body["due_date"] = due_date
    return await work.create_ticket(team_id, project_id, body, get_auth_headers(ctx))


@mcp.tool()
@tool_errors
async def move_ticket(
    team_id: str, project_id: str, ticket: str, status: Status, ctx: Context
) -> dict:
    """Change a ticket's status (its board column).

    status is one of backlog, todo, in_progress, in_review, done.
    ticket is a ticket key like DB-67 or the ticket's id.
    """
    headers = get_auth_headers(ctx)
    ticket_id = await work.resolve_ticket_id(team_id, project_id, ticket, headers)
    return await work.update_ticket(
        team_id, project_id, ticket_id, {"status": status}, headers
    )


@mcp.tool()
@tool_errors
async def assign_ticket(
    team_id: str,
    project_id: str,
    ticket: str,
    assignee_id: str | None,
    ctx: Context,
) -> dict:
    """Assign a ticket to a project member by user id, or pass null to unassign.

    Assigning someone other than yourself needs the Project Lead role.
    ticket is a ticket key like DB-67 or the ticket's id.
    """
    headers = get_auth_headers(ctx)
    ticket_id = await work.resolve_ticket_id(team_id, project_id, ticket, headers)
    return await work.update_ticket(
        team_id,
        project_id,
        ticket_id,
        {"assignee_id": assignee_id},
        headers,
    )


@mcp.tool()
@tool_errors
async def whoami(ctx: Context) -> dict:
    """Return the current DevBoard user: user_id, username, email and role.

    Use user_id as assignee_id to assign a ticket to yourself.
    """
    me = await work.get_me(get_auth_headers(ctx))
    return {
        "user_id": me["user_id"],
        "username": me["username"],
        "email": me["email"],
        "role": me["role"],
    }


@mcp.tool()
@tool_errors
async def comment_on_ticket(
    team_id: str, project_id: str, ticket: str, body: str, ctx: Context
) -> dict:
    """Add a comment to a ticket.

    ticket is a ticket key like DB-67 or the ticket's id.
    """
    headers = get_auth_headers(ctx)
    ticket_id = await work.resolve_ticket_id(team_id, project_id, ticket, headers)
    return await work.create_comment(team_id, project_id, ticket_id, body, headers)


@mcp.tool()
@tool_errors
async def list_project_members(
    team_id: str, project_id: str, ctx: Context, limit: int = 50, offset: int = 0
) -> dict:
    """List a project's members with username and role.

    user_id is what assign_ticket needs as assignee_id.
    """
    headers = get_auth_headers(ctx)
    page = await work.list_project_members(team_id, project_id, headers, limit, offset)
    users = await work.lookup_users([m["user_id"] for m in page["results"]], headers)
    names = {u["user_id"]: u["username"] for u in users}
    page["results"] = [
        {
            "user_id": m["user_id"],
            "username": names.get(m["user_id"]),
            "role": m["role"],
        }
        for m in page["results"]
    ]
    return page
