import secrets
import time

from mcp.server.auth.provider import construct_redirect_uri
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response

from app.clients import auth
from app.exceptions import LoginFailedException, ServiceUnavailableException
from app.mcp_server import mcp
from app.oauth import store
from app.oauth.login_page import render_login_page, render_message_page
from app.oauth.models import DevBoardAuthorizationCode, PendingAuthorization

EXPIRED_MESSAGE = "This login link expired. Go back to Claude Code and try again."
UNAVAILABLE_MESSAGE = "DevBoard login is unavailable. Try again in a moment."

SECURITY_HEADERS = {
    "Cache-Control": "no-store",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": (
        "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'"
    ),
}


def _html(content: str, status_code: int = 200) -> HTMLResponse:
    return HTMLResponse(content, status_code=status_code, headers=SECURITY_HEADERS)


async def _requester(pending: PendingAuthorization) -> str:
    client = await store.get_client(pending.client_id)
    name = (client.client_name if client else None) or "An application"
    return f"{name} ({pending.params.redirect_uri.host})"


def _issue_code(
    pending: PendingAuthorization, tokens: dict
) -> DevBoardAuthorizationCode:
    params = pending.params
    return DevBoardAuthorizationCode(
        code=secrets.token_urlsafe(32),
        scopes=params.scopes or [],
        expires_at=time.time() + store.CODE_TTL_SECONDS,
        client_id=pending.client_id,
        code_challenge=params.code_challenge,
        redirect_uri=params.redirect_uri,
        redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
        resource=params.resource,
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        expires_in=tokens["expires_in"],
    )


@mcp.custom_route("/login", methods=["GET"])
async def login_form(request: Request) -> Response:
    session = request.query_params.get("session", "")
    pending = await store.get_pending(session)
    if pending is None:
        return _html(render_message_page(EXPIRED_MESSAGE), 400)
    return _html(render_login_page(session, await _requester(pending)))


@mcp.custom_route("/login", methods=["POST"])
async def login_submit(request: Request) -> Response:
    form = await request.form()
    session = str(form.get("session", ""))
    email = str(form.get("email", ""))
    password = str(form.get("password", ""))

    pending = await store.get_pending(session)
    if pending is None:
        return _html(render_message_page(EXPIRED_MESSAGE), 400)

    try:
        tokens = await auth.login(email, password)
    except LoginFailedException as exc:
        error = str(exc) or "Login failed."
        page = render_login_page(session, await _requester(pending), error)
        return _html(page, 401)
    except ServiceUnavailableException:
        page = render_login_page(
            session, await _requester(pending), UNAVAILABLE_MESSAGE
        )
        return _html(page, 502)

    if await store.pop_pending(session) is None:
        return _html(render_message_page(EXPIRED_MESSAGE), 400)

    code = _issue_code(pending, tokens)
    await store.save_code(code)
    redirect_url = construct_redirect_uri(
        str(pending.params.redirect_uri), code=code.code, state=pending.params.state
    )
    return RedirectResponse(redirect_url, status_code=303, headers=SECURITY_HEADERS)