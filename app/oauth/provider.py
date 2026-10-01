from urllib.parse import urlencode

import jwt
from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationParams,
    OAuthAuthorizationServerProvider,
    RefreshToken,
    TokenError,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

from app.clients import auth
from app.config import settings
from app.exceptions import RefreshRejectedException
from app.oauth import store
from app.oauth.models import DevBoardAuthorizationCode, PendingAuthorization

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_CLIENT_ID = "devboard"


class DevBoardOAuthProvider(
    OAuthAuthorizationServerProvider[
        DevBoardAuthorizationCode, RefreshToken, AccessToken
    ]
):
    """OAuth server for Claude Code that hands out DevBoard's own tokens.

    Accounts, passwords and token signing stay in devboard-auth.
    """

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        return await store.get_client(client_id)

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        await store.save_client(client_info)

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        session_id = await store.save_pending(
            PendingAuthorization(client_id=client.client_id, params=params)
        )
        query = urlencode({"session": session_id})
        return f"{settings.PUBLIC_URL.rstrip('/')}/login?{query}"

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> DevBoardAuthorizationCode | None:
        return await store.pop_code(authorization_code)

    async def exchange_authorization_code(
        self,
        client: OAuthClientInformationFull,
        authorization_code: DevBoardAuthorizationCode,
    ) -> OAuthToken:
        await store.bind_refresh_token(authorization_code.refresh_token, client.client_id)
        return OAuthToken(
            access_token=authorization_code.access_token,
            expires_in=authorization_code.expires_in,
            refresh_token=authorization_code.refresh_token,
            scope=" ".join(authorization_code.scopes) or None,
        )

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> RefreshToken | None:
        if await store.get_refresh_client_id(refresh_token) != client.client_id:
            return None
        return RefreshToken(token=refresh_token, client_id=client.client_id, scopes=[])

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        try:
            tokens = await auth.refresh(refresh_token.token)
        except RefreshRejectedException as exc:
            await store.unbind_refresh_token(refresh_token.token)
            raise TokenError("invalid_grant", "DevBoard rejected the refresh token") from exc

        await store.unbind_refresh_token(refresh_token.token)
        await store.bind_refresh_token(tokens["refresh_token"], client.client_id)
        return OAuthToken(
            access_token=tokens["access_token"],
            expires_in=tokens["expires_in"],
            refresh_token=tokens["refresh_token"],
            scope=" ".join(scopes) or None,
        )

    async def load_access_token(self, token: str) -> AccessToken | None:
        try:
            claims = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[JWT_ALGORITHM],
                options={"require": ["exp", "sub"]},
            )
        except jwt.InvalidTokenError:
            return None
        return AccessToken(
            token=token,
            client_id=ACCESS_TOKEN_CLIENT_ID,
            scopes=[],
            expires_at=int(claims["exp"]),
            subject=claims["sub"],
        )

    async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
        # Access tokens are stateless JWTs and expire on their own; only the
        # refresh token can actually be revoked.
        if isinstance(token, RefreshToken):
            await auth.logout(token.token)
            await store.unbind_refresh_token(token.token)