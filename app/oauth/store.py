import secrets

from mcp.shared.auth import OAuthClientInformationFull

from app.oauth.models import DevBoardAuthorizationCode, PendingAuthorization
from app.redis_client import get_redis

PENDING_TTL_SECONDS = 600
CODE_TTL_SECONDS = 60


def _key(kind: str, key_id: str) -> str:
    return f"mcp:oauth:{kind}:{key_id}"


async def save_client(client: OAuthClientInformationFull) -> None:
    await get_redis().set(_key("client", client.client_id), client.model_dump_json())


async def get_client(client_id: str) -> OAuthClientInformationFull | None:
    raw = await get_redis().get(_key("client", client_id))
    return OAuthClientInformationFull.model_validate_json(raw) if raw else None


async def save_pending(pending: PendingAuthorization) -> str:
    session_id = secrets.token_urlsafe(32)
    await get_redis().set(
        _key("pending", session_id), pending.model_dump_json(), ex=PENDING_TTL_SECONDS
    )
    return session_id


async def get_pending(session_id: str) -> PendingAuthorization | None:
    raw = await get_redis().get(_key("pending", session_id))
    return PendingAuthorization.model_validate_json(raw) if raw else None


async def pop_pending(session_id: str) -> PendingAuthorization | None:
    raw = await get_redis().getdel(_key("pending", session_id))
    return PendingAuthorization.model_validate_json(raw) if raw else None


async def save_code(code: DevBoardAuthorizationCode) -> None:
    await get_redis().set(
        _key("code", code.code), code.model_dump_json(), ex=CODE_TTL_SECONDS
    )


async def pop_code(code: str) -> DevBoardAuthorizationCode | None:
    raw = await get_redis().getdel(_key("code", code))
    return DevBoardAuthorizationCode.model_validate_json(raw) if raw else None