import logging
import uuid

import httpx

from app.clients.common import response_detail
from app.config import settings
from app.exceptions import (
    ForbiddenException,
    InvalidRequestException,
    NotFoundException,
    ServiceUnavailableException,
    UnauthorizedException,
)
from app.http_client import get_http_client

logger = logging.getLogger(__name__)


async def _request(
    method: str,
    path: str,
    headers: dict[str, str],
    params: dict | None = None,
    json: dict | None = None,
):
    try:
        response = await get_http_client().request(
            method, path, headers=headers, params=params, json=json
        )
    except httpx.HTTPError as exc:
        logger.error("Work service request failed: %s", exc)
        raise ServiceUnavailableException()

    status = response.status_code
    if status < 400:
        return response.json()
    if status == 401:
        raise UnauthorizedException()
    if status == 403:
        raise ForbiddenException()
    if status == 404:
        raise NotFoundException(response_detail(response))
    if status in (400, 409, 422):
        raise InvalidRequestException(response_detail(response))
    logger.error("Work service returnded %s for GET %s", status, path)
    raise ServiceUnavailableException()


def _tickets_path(team_id: str, project_id: str) -> str:
    return f"/api/teams/{team_id}/projects/{project_id}/tickets/"


async def list_teams(headers: dict[str, str], limit: int = 50, offset: int = 0):
    return await _request(
        "GET", "/api/teams/", headers, {"limit": limit, "offset": offset}
    )


async def list_projects(
    team_id: str, headers: dict[str, str], limit: int = 50, offset: int = 0
):
    return await _request(
        "GET",
        f"/api/teams/{team_id}/projects/",
        headers,
        {"limit": limit, "offset": offset},
    )


async def list_tickets(
    team_id: str,
    project_id: str,
    headers: dict[str, str],
    limit: int = 50,
    offset: int = 0,
):
    return await _request(
        "GET",
        f"/api/teams/{team_id}/projects/{project_id}/tickets/",
        headers,
        {"limit": limit, "offset": offset},
    )


async def get_ticket(
    team_id: str, project_id: str, ticket_id: str, headers: dict[str, str]
):
    return await _request(
        "GET", f"{_tickets_path(team_id, project_id)}{ticket_id}/", headers
    )


async def create_ticket(
    team_id: str, project_id: str, body: dict, headers: dict[str, str]
):
    return await _request(
        "POST",
        _tickets_path(team_id, project_id),
        headers,
        json=body,
    )


async def update_ticket(
    team_id: str, project_id: str, ticket_id: str, body: dict, headers: dict[str, str]
):
    return await _request(
        "PATCH", f"{_tickets_path(team_id, project_id)}{ticket_id}/", headers, json=body
    )


async def create_comment(
    team_id: str, project_id: str, ticket_id: str, body: str, headers: dict[str, str]
):
    return await _request(
        "POST",
        f"{_tickets_path(team_id, project_id)}{ticket_id}/comments/",
        headers,
        json={"body": body},
    )


async def resolve_ticket_id(
    team_id: str, project_id: str, ticket: str, headers: dict[str, str]
) -> str:
    """Check if it's an ID, if not then pass because it is the KEY"""
    try:
        return str(uuid.UUID(ticket))
    except ValueError:
        pass
    data = await _request(
        "GET",
        _tickets_path(team_id, project_id),
        headers,
        params={"key": ticket, "limit": 1},
    )
    if not data["results"]:
        raise NotFoundException(f"Ticket {ticket} not found in this project.")
    return data["results"][0]["id"]


async def get_me(headers: dict[str, str]) -> dict:
    return await _request(
        "GET", f"{settings.CORE_URL.rstrip('/')}/api/users/me/", headers
    )


async def list_project_members(
    team_id: str,
    project_id: str,
    headers: dict[str, str],
    limit: int = 50,
    offset: int = 0,
):
    return await _request(
        "GET",
        f"/api/teams/{team_id}/projects/{project_id}/members/",
        headers,
        params={"limit": limit, "offset": offset},
    )


async def lookup_users(user_ids: list[str], headers: dict[str, str]) -> list[dict]:
    if not user_ids:
        return []
    return await _request(
        "POST",
        f"{settings.CORE_URL.rstrip('/')}/api/users/batch/",
        headers,
        json={"ids": user_ids},
    )
