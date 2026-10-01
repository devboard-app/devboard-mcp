from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationParams,
    OAuthAuthorizationServerProvider,
    RefreshToken,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

from app.oauth import store
from app.oauth.models import DevBoardAuthorizationCode


class DevBoardOAuthProvider(
    OAuthAuthorizationServerProvider[
        DevBoardAuthorizationCode, RefreshToken, AccessToken
    ]
):
    def __init__(self) -> None:
        self._clients: dict[str, OAuthClientInformationFull] = {}

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        return await store.get_client(client_id)

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        await store.save_client(client_info)

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        raise NotImplementedError("Step 3")

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> DevBoardAuthorizationCode | None:
        raise NotImplementedError("Step 4")

    async def exchange_authorization_code(
        self,
        client: OAuthClientInformationFull,
        authorization_code: DevBoardAuthorizationCode,
    ) -> OAuthToken:
        raise NotImplementedError("Step 4")

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> RefreshToken | None:
        raise NotImplementedError("Step 4")

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        raise NotImplementedError("Step 4")

    async def load_access_token(self, token: str) -> AccessToken | None:
        return AccessToken(token=token, client_id="spike", scopes=[])
