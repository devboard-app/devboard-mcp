from mcp.server.auth.provider import AuthorizationCode, AuthorizationParams
from pydantic import BaseModel


class PendingAuthorization(BaseModel):
    """An /authorize request waiting for the user to log in."""

    client_id: str
    params: AuthorizationParams


class DevBoardAuthorizationCode(AuthorizationCode):
    """The SDK's auth code, plus the DevBoard tokens issued at login."""

    access_token: str
    refresh_token: str
    expires_in: int
