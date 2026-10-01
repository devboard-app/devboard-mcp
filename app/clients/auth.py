import logging

import httpx

from app.clients.common import response_detail
from app.config import settings
from app.exceptions import (
    LoginFailedException,
    RefreshRejectedException,
    ServiceUnavailableException,
)
from app.http_client import get_http_client

logger = logging.getLogger(__name__)


async def _post(path: str, payload: dict) -> httpx.Response:
    try:
        return await get_http_client().post(
            f"{settings.AUTH_URL.rstrip('/')}/auth{path}", json=payload
        )
    except httpx.HTTPError as exc:
        logger.error("Auth service request failed: %s", exc)
        raise ServiceUnavailableException from exc


async def login(email: str, password: str) -> dict:
    response = await _post("/login/", {"email": email, "password": password})
    if response.status_code == 200:
        return response.json()
    if response.status_code in (401, 403, 429):
        raise LoginFailedException(response_detail(response) or "")
    logger.error("Auth service returned %s for POST /login/", response.status_code)
    raise ServiceUnavailableException


async def refresh(refresh_token: str) -> dict:
    response = await _post("/refresh-token/", {"refresh_token": refresh_token})
    if response.status_code == 200:
        return response.json()
    if response.status_code in (401, 403):
        raise RefreshRejectedException
    logger.error(
        "Auth service returned %s for POST /refresh-token/", response.status_code
    )
    raise ServiceUnavailableException


async def logout(refresh_token: str) -> None:
    response = await _post("/logout/", {"refresh_token": refresh_token})
    if response.status_code >= 500:
        logger.error("Auth service returned %s for POST /logout/", response.status_code)
        raise ServiceUnavailableException
