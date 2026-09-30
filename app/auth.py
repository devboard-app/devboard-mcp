from mcp.server.mcpserver import Context

from app.exceptions import MissingTokenException


def get_auth_headers(ctx: Context) -> dict[str, str]:
    request = ctx.request_context.request
    value = request.headers.get("authorization", "") if request else ""
    if not value.lower().startswith("bearer ") or not value[7:].strip():
        raise MissingTokenException("Missing bearer token")
    return {"Authorization": value}
