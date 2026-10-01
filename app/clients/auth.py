import logging

import httpx

from app.clients.common import response_detail
from app.config import settings
from app.exceptions import LoginFailedException, ServiceUnavailableException
from app.http_client import get_http_client

logger = logging.getLogger(__name__)


async def login(email: str, password: str) -> dict:
    """Log in through devboard-auth. Returns access_token, refresh_token, expires_in."""
    try:
        response = await get_http_client().post(
            f"{settings.AUTH_URL.rstrip('/')}/auth/login/",
            json={"email": email, "password": password},
        )
    except httpx.HTTPError as exc:
        logger.error("Auth service request failed: %s", exc)
        raise ServiceUnavailableException from exc

    if response.status_code == 200:
        return response.json()
    if response.status_code in (401, 403, 429):
        raise LoginFailedException(response_detail(response) or "")
    logger.error("Auth service returned %s for POST /login/", response.status_code)
    raise ServiceUnavailableException